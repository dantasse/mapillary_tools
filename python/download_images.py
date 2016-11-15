import urllib2, urllib
import json
import os
import shutil
import argparse, geojson, shapely.geometry

MAPILLARY_API_IM_SEARCH_URL = 'https://a.mapillary.com/v1/im/search?'


'''
Script to download images using the Mapillary image search API.

Downloads images for each neighborhood within a city. (specified by a geojson
file.)
'''

def create_dirs(base_path):
    try:
        shutil.rmtree(base_path)
    except:
        pass
    os.makedirs(base_path)


def query_search_api(min_lat, max_lat, min_lon, max_lon, max_results):
    '''
    Send query to the search API and get dict with image data.
    '''
    params = urllib.urlencode(zip(['min-lat', 'max-lat', 'min-lon', 'max-lon', 'max-results'],[min_lat, max_lat, min_lon, max_lon, max_results]))
    query = urllib2.urlopen(MAPILLARY_API_IM_SEARCH_URL + params).read()
    query = json.loads(query)
    print("Result: {0} images in area.".format(len(query)))
    return query


def download_images(query, path, size=1024):
    '''
    Download images in query result to path.

    Return list of downloaded images with lat,lon.
    There are four sizes available: 320, 640, 1024 (default), or 2048.
    '''
    im_size = "thumb-{0}.jpg".format(size)
    im_list = []

    for im in query:
        url = im['image_url']+im_size
        filename = im['key']+".jpg"
        try:
            image = urllib.URLopener()
            image.retrieve(url, path+filename)
            im_list.append([filename, str(im['lat']), str(im['lon'])])
            print("Successfully downloaded: {0}".format(filename))
        except KeyboardInterrupt:
            break
        except:
            print("Failed to download: {0}".format(filename))
    return im_list


if __name__ == '__main__':
    '''
    Use from command line as below, or run query_search_api and download_images
    from your own scripts.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('--city_name', default='pgh')
    parser.add_argument('--max_results', default=1000)
    parser.add_argument('--neighborhoods_file', default='nghd_bounds.geojson')
    parser.add_argument('--image_size', type=int, default=1024, choices=[320,640,1024,2048])
    args = parser.parse_args()

    nghds = geojson.load(open(args.neighborhoods_file))['features']
    for nghd in nghds:
        nghd_name = nghd['properties']['name']
        nghd_shape = shapely.geometry.asShape(nghd['geometry'])
        min_lon, min_lat, max_lon, max_lat = nghd_shape.bounds

        # query api
        query = query_search_api(min_lat, max_lat, min_lon, max_lon, args.max_results)
        if len(query) == args.max_results:
            pass # TODO do something b/c you might be missing some.

        nghd_dir = args.city_name + "/" + nghd_name + "/"
        # create directories for saving
        create_dirs(nghd_dir)

        # download
        # downloaded_list = download_images(query, path=nghd_dir, size=args.image_size)
        im_size = "thumb-{0}.jpg".format(args.image_size)
        downloaded_list = []

        for im in query:
            if shapely.geometry.Point(im['lon'], im['lat']).within(nghd_shape):
                url = im['image_url']+im_size
                filename = im['key']+".jpg"
                try:
                    print nghd_dir+filename
                    image = urllib.URLopener()
                    image.retrieve(url, nghd_dir+filename)
                    downloaded_list.append([filename, str(im['lat']), str(im['lon'])])
                    print("Successfully downloaded: {0}".format(filename))
                except KeyboardInterrupt:
                    break
                except:
                    print("Failed to download: {0}".format(filename))


        # save filename with lat, lon
        with open(nghd_dir+"downloaded.txt", "w") as f:
            for data in downloaded_list:
                f.write(",".join(data) + "\n")
