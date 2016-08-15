import urllib.request
import urllib3
import img2pdf
import re
import os
import argparse
from bs4 import BeautifulSoup
from PIL import Image
from resizeimage import resizeimage

def parse_url_to_manga_info(url):
    url = re.sub('http://', '', url)
    url = re.sub('mangapark.me/manga/', '', url)
    title = url.split("/")[0]
    return title


def parse_url_to_chapter_info(url):
    url = re.sub("http://", '', url)
    url = re.sub("mangapark.me", '', url)
    url = re.sub("/manga/", '', url)
    title, _, version, chapter = url.split("/")
    return title, version, chapter, url


def ensure_directory_exist(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def input_images(path):
    if path == '-':
        rawdata = sys.stdin.buffer.read()
    else:
        try:
            with open(path, "rb") as im:
                rawdata = im.read()
        except IsADirectoryError:
            raise argparse.ArgumentTypeError(
                "\"%s\" is a directory" % path)
        except PermissionError:
            raise argparse.ArgumentTypeError(
                "\"%s\" permission denied" % path)
        except FileNotFoundError:
            raise argparse.ArgumentTypeError(
                "\"%s\" does not exist" % path)
    if len(rawdata) == 0:
        raise argparse.ArgumentTypeError("\"%s\" is empty" % path)
    return rawdata


def convert_to_pdf(os_dir, chapter, filenames):
    print("Converting chapter %s to pdf..." % chapter)
    pdf_bytes = img2pdf.convert(*[input_images(path) for path in filenames])
    file = open("%s/%s.pdf" % (os_dir, chapter), "wb")
    file.write(pdf_bytes)
    print("Conversion completed!")


def download_chapter(url, height):
    title, version, chapter, os_dir = parse_url_to_chapter_info(url)
    ensure_directory_exist(os_dir)
    try:
        page = urllib.request.urlopen(url)
    except ValueError as e:
        page = urllib.request.urlopen("http://mangapark.me" + url)

    soup = BeautifulSoup(page, "html.parser")
    imgs_wrappers = soup.find_all("a", {"class": "img-link"})
    filenames = []
    for i in imgs_wrappers:
        img_url = i.img['src']
        filename = img_url.split('/')[-1]
        print("Downloading %s %s %s..." % (title, chapter, filename))
        dir_filename = os_dir + "/" + os.path.basename(img_url)
        urllib.request.urlretrieve(img_url, dir_filename)
        new_dir_filename = rezise(dir_filename, height)
        filenames.append(new_dir_filename)

    convert_to_pdf(os_dir, chapter, filenames)

def rezise(filename, height):
    if height == None:
        return filename
    print("Resizing %s to %spx height..." % (filename, height))
    with open(filename, 'r+b') as f:
        with Image.open(f) as image:
            cover = resizeimage.resize_height(image, height)
            new_filename = filename + '.res';
            cover.save(new_filename, image.format)
    return new_filename

def download_manga(url, chapter=False, min_max=False, height=None):
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, "html.parser")

    streams = soup.find_all("div", {"class": "stream"})
    stream_lens = []
    for stream in streams:
        chapters = stream.find_all("li")
        stream_lens += [len(chapters)]

    max_stream_len = max(stream_lens)
    max_idx = stream_lens.index(max_stream_len)
    best_stream = streams[max_idx]

    chapters = best_stream.find_all("li")
    for c in chapters[::-1]:
        chapter_url = c.em.find_all("a")[-1]['href']
        chapter_no = float(parse_url_to_chapter_info(chapter_url)[2][1: ])
        if chapter and chapter_no == chapter:
            download_chapter(chapter_url, height)
            break
        if min_max and chapter_no >= min_max[0] and chapter_no <= min_max[1]:
            download_chapter(chapter_url, height)
            continue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--manga-url')
    parser.add_argument('-s', '--size', '--height', type=int, help='Height to resize images to (it will keet the aspect ratio)')
    parser.add_argument('-c', '--chapter')
    parser.add_argument('-cs', '--chapters', nargs = 2)

    args = parser.parse_args()
    print(args)
    if args.manga_url == None:
        print("Please specify the URL of the manga on mangapark.me")
        return
    elif args.chapters != None:
        assert isinstance(args.chapters, list)
        download_manga(args.manga_url, min_max=[float(x) for x in args.chapters], height=args.size)
    elif args.chapter != None:
        download_manga(args.manga_url, chapter=int(args.chapter), height=args.size)


if __name__ == "__main__":
    main()
