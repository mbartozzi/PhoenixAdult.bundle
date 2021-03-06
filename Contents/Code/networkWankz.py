import PAsearchSites
import PAgenres
import PAutils


def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    req = PAutils.HTTPRequest(PAsearchSites.getSearchSearchURL(siteNum) + encodedTitle)
    searchResults = HTML.ElementFromString(req.text)
    for searchResult in searchResults.xpath('//div[@class="scene"]'):
        titleNoFormatting = searchResult.xpath('.//div[@class="title-wrapper"]//a[@class="title"]')[0].text_content()
        curID = PAutils.Encode(searchResult.xpath('.//a/@href')[0])
        subSite = searchResult.xpath('.//div[@class="series-container"]//a[@class="sitename"]')[0].text_content()

        siteScore = 80 - (Util.LevenshteinDistance(subSite.lower(), PAsearchSites.getSearchSiteName(siteNum).lower()) * 8 / 10)
        titleScore = 20 - (Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower()) * 2 / 10)
        score = siteScore + titleScore

        results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name='%s [%s]' % (titleNoFormatting, subSite), score=score, lang=lang))

    return results


def update(metadata, siteID, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneURL = PAutils.Decode(metadata_id[0])
    if not sceneURL.startswith('http'):
        sceneURL = PAsearchSites.getSearchBaseURL(siteID) + sceneURL
    req = PAutils.HTTPRequest(sceneURL)
    detailsPageElements = HTML.ElementFromString(req.text)

    # Title
    metadata.title = detailsPageElements.xpath('//h1[@class="detail__title"]')[0].text_content().strip()

    # Summary
    metadata.summary = detailsPageElements.xpath('//div[@class="detail__txt detail__txt-show_lg"]')[0].text_content()

    # Studio
    metadata.studio = 'Wankz'

    # Release Date
    date = detailsPageElements.xpath('//span[@class="detail__date"]')[0].text_content().strip()
    date_object = parse(date)
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year

    # Actors
    movieActors.clearActors()
    for actor in detailsPageElements.xpath('//div[@class="detail__models"]//a'):
        actorName = actor.text_content().strip()
        actorPhotoURL = ''

        movieActors.addActor(actorName, actorPhotoURL)

    # Genres
    movieGenres.clearGenres()
    for genreLink in detailsPageElements.xpath('//a[@class="tag"]'):
        genreName = genreLink.text_content().strip()

        movieGenres.addGenre(genreName)

    # Posters/Background
    art = []
    xpaths = [
        '//meta[@property="og:image"]/@content',
        '//div[@class="photo-strip__slide"]/@data-src'
    ]
    for xpath in xpaths:
        for poster in detailsPageElements.xpath(xpath):
            art.append(poster)

    Log('Artwork found: %d' % len(art))
    for idx, posterUrl in enumerate(art, 1):
        if not PAsearchSites.posterAlreadyExists(posterUrl, metadata):
            # Download image file for analysis
            try:
                image = PAutils.HTTPRequest(posterUrl, headers={'Referer': 'http://www.google.com'})
                im = StringIO(image.content)
                resized_image = Image.open(im)
                width, height = resized_image.size
                # Add the image proxy items to the collection
                if width > 1:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx)
                if width > 100:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx)
            except:
                pass

    return metadata
