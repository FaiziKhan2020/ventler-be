import requests
import json
import time

async def upload_to_wordpress(title, payload,slug, url, creds, username, author=None, category=None,preview_image_link=None):
    #process payload here
    try:
        if url[len(url)-1] == '/':
            url = url[:-1]
        authorId = None
        categoryId = None
        if category is not None:
            req = requests.get(url+"/wp-json/wp/v2/categories?context=view", auth=(username, creds))
            dat = req.json()
            for rec in dat:
                if rec is not None and rec['name'] == category:
                    categoryId = rec['id']
        if author is not None:
            req = requests.get(url+"/wp-json/wp/v2/users?context=view&who=authors", auth=(username, creds))
            dat = req.json()
            for rec in dat:
                if rec is not None and rec['name'] == author:
                    authorId = rec['id']
        data = {
            'title':title,
            'content': payload,
            'status': 'publish',
            'slug': slug
        }
        if authorId is not None:
            data["author"] = authorId
        if categoryId is not None:
            data["categories"] = [categoryId]
        media_upload_id =  None
        if preview_image_link is not None and preview_image_link != "":
            with requests.get(preview_image_link, stream=True) as response:
                if response.status_code == 200:
                    media_upload_endpoint = url + "/wp-json/wp/v2/media"
                    files = {'file': (preview_image_link, response.content)}
                    headers = {
                        "Content-Disposition": f"attachment; filename={int(time.time())}.jpg",
                    }
                    media_response = requests.post(media_upload_endpoint,auth=(username, creds), headers=headers, files=files)
                    if media_response.status_code == 201:
                        media_data = media_response.json()
                        media_upload_id = media_data["id"]
                    else:
                        print("Error uploading media.")
                else:
                    print("Error fetching image.")
        if media_upload_id is not None:
            data["featured_media"] = media_upload_id
        fin_url = url+"/wp-json/wp/v2/posts"
        response = requests.post(fin_url, auth=(username, creds), json=data)
        if response.status_code != 201:
            raise Exception("Post not published")
        return response.json().get('guid').get('rendered')
    except Exception as err:
        print("Err, ",str(err))
        return str(err)