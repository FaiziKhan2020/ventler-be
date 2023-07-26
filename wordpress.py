import requests
import json

async def upload_to_wordpress(title, payload,slug, url, creds, username):
    #process payload here
    print("ddddd")
    try:
        print("I am uploading")
        data = {
            'title':title,
            'content': payload,
            'status': 'published',
            'slug': slug
        }
        if url[len(url)-1] == '/':
            url = url[:-1]
        fin_url = url+"/wp-json/wp/v2/posts"
        print(fin_url)
        response = requests.post(fin_url, auth=(username, creds), json=data)
        print(response.reason)
        print(response.json())
        if response.status_code != 201:
            raise Exception("Post not published")
        print("uploaded")
        return true
    except Exception as err:
        print("Err")
        return str(err)