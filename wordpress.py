import requests
import json

async def upload_to_wordpress(title, payload,slug, url, creds, username, author=None):
    #process payload here
    print("ddddd")
    try:
        print("I am uploading")
        if url[len(url)-1] == '/':
            url = url[:-1]
        authorId = None
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
        
        
        fin_url = url+"/wp-json/wp/v2/posts"
        response = requests.post(fin_url, auth=(username, creds), json=data)
        if response.status_code != 201:
            raise Exception("Post not published")
        print("uploaded at: ", response.json().get('guid').get('rendered'))
        return response.json().get('guid').get('rendered')
    except Exception as err:
        print("Err")
        return str(err)