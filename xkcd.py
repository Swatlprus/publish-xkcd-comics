import requests
import random
import os
from environs import Env


def find_errors_vk(response):
    if response['error']:
        error_code = response['error']['error_code']
        error_msg = response['error']['error_msg']
        raise requests.HTTPError(error_code, error_msg)


def get_random_number():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    xkcd_response = response.json()
    return random.randint(1, xkcd_response['num'])


def download_xkcd(xkcd_number):
    url = f'https://xkcd.com/{xkcd_number}/info.0.json'
    filename = 'comics_xkcd.png'
    response = requests.get(url)
    response.raise_for_status()
    xkcd_response = response.json()
    img_response = requests.get(xkcd_response['img'])
    img_response.raise_for_status()
    alt_text = xkcd_response['alt']
    with open(filename, 'wb') as file:
        file.write(img_response.content)
    return alt_text, filename


def get_upload_url(token_vk, group_id):
    url = 'https://api.vk.com/method/photos.getWallUploadServer/'
    params = {
        'access_token': token_vk,
        'group_id': group_id,
        'v': '5.131'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    upload_response = response.json()
    find_errors_vk(upload_response)
    return upload_response['response']['upload_url']


def upload_img(upload_url, filename):
    with open(filename, 'rb') as file:
        url = upload_url
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
    response.raise_for_status()
    upload_response = response.json()
    find_errors_vk(upload_response)
    server = upload_response['server']
    photo = upload_response['photo']
    vk_hash = upload_response['hash']
    return server, photo, vk_hash


def save_wall_photo(token_vk, group_id, server, photo, vk_hash):
    url_for_save = 'https://api.vk.com/method/photos.saveWallPhoto/'
    params = {
        'access_token': token_vk,
        'group_id': group_id,
        'v': '5.131',
        'server': server,
        'photo': photo,
        'hash': vk_hash
    }
    response = requests.post(url_for_save, params=params)
    response.raise_for_status()
    save_vk_response = response.json()
    find_errors_vk(save_vk_response)
    owner_id = save_vk_response['response'][0]['owner_id']
    media_id = save_vk_response['response'][0]['id']
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
    publish_response = requests.post(url, params=params)
    publish_response.raise_for_status()
    publish_xkcd_response = publish_response.json()
    find_errors_vk(publish_xkcd_response)
    os.remove(filename)


def main():
    env = Env()
    env.read_env()
    token_vk = env("VK_TOKEN")
    vk_group_id = env("VK_GROUP_ID")
    xkcd_number = get_random_number()
    try:
        alt_text, filename = download_xkcd(xkcd_number)
        upload_url = get_upload_url(token_vk, vk_group_id)
        server, photo, vk_hash = upload_img(upload_url, filename)
        attachments = save_wall_photo(token_vk, vk_group_id, server, photo, vk_hash)
        publish_comics(token_vk, vk_group_id, attachments, alt_text, filename)
    except ValueError:
        print('Value Error')
        os.remove(filename)
    except KeyError:
        print('Key Error')
        os.remove(filename)


if __name__ == "__main__":
    main()