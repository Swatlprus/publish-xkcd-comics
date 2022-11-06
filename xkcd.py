import requests
import random
import os
from environs import Env


def get_random_number():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    response_xkcd = response.json()
    return random.randint(1, response_xkcd['num'])


def download_xkcd(number_xkcd):
    url = f'https://xkcd.com/{number_xkcd}/info.0.json'
    filename = 'comics_xkcd.png'
    response = requests.get(url)
    response.raise_for_status()
    response_xkcd = response.json()
    response_img = requests.get(response_xkcd['img'])
    response_img.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response_img.content)
    alt_text = response_xkcd['alt']
    return [alt_text, filename]


def get_upload_url(token_vk, group_id):
    url = 'https://api.vk.com/method/photos.getWallUploadServer/'
    params = {
        'access_token': token_vk,
        'group_id': group_id,
        'v': '5.131'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    response_upload = response.json()
    return response_upload['response']['upload_url']


def upload_img(upload_url, filename):
    with open(filename, 'rb') as file:
        url = upload_url
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        response_upload = response.json()
        server = response_upload['server']
        photo = response_upload['photo']
        hash = response_upload['hash']
        return [server, photo, hash]


def save_wall_photo(token_vk, group_id, server_photo_hash):
    server, photo, hash = server_photo_hash
    url_for_save = 'https://api.vk.com/method/photos.saveWallPhoto/'
    params = {
        'access_token': token_vk,
        'group_id': group_id,
        'v': '5.131',
        'server': server,
        'photo': photo,
        'hash': hash
    }
    response = requests.post(url_for_save, params=params)
    response.raise_for_status()
    response_save_vk = response.json()
    owner_id = response_save_vk['response'][0]['owner_id']
    media_id = response_save_vk['response'][0]['id']
    attachments = f'photo{owner_id}_{media_id}'
    return attachments


def publish_comics(token_vk, group_id, attachments, alt_text, filename):
    url = 'https://api.vk.com/method/wall.post/'
    params = {
        'access_token': token_vk,
        'v': '5.131',
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'attachments': attachments,
        'message': alt_text
    }
    response_publish = requests.post(url, params=params)
    response_publish.raise_for_status()
    os.remove(filename)


def main():
    env = Env()
    env.read_env()
    token_vk = env("VK_TOKEN")
    group_id = env("GROUP_ID")
    number_xkcd = get_random_number()
    alt_text, filename = download_xkcd(number_xkcd)
    upload_url = get_upload_url(token_vk, group_id)
    server_photo_hash = upload_img(upload_url, filename)
    attachments = save_wall_photo(token_vk, group_id, server_photo_hash)
    publish_comics(token_vk, group_id, attachments, alt_text, filename)


if __name__ == "__main__":
    main()