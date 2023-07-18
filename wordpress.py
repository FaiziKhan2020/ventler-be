import requests
import json

async def upload_to_wordpress(title, payload, url, creds, username):
    #process payload here
    try:
        data = {
            'title':title,
            'content': payload,
            'status': 'draft'
        }
        response = requests.post(f"{url}wp-json/wp/v2/posts", auth=(username, creds), json=data)
        if response.status_code != 201:
            raise Exception("Post not published")
        print("uploaded")
        return true
    except Exception as err:
        return str(err)