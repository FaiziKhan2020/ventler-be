import openai
import requests
import json

async def gpt_rewrite(title,text,summary, openai_key, user_prompt = None, images = [], stable_diff_key = ""):
    openai.api_key = openai_key
    final_article = ""
    print('B000')
    # re-write conent
    base_prompt = "You should act as a highly professional Korean blog writer, you would be given article text as input and YOU SHOULD using your own knowledge of that domain discussed in the input text write a large content as detailed as possible and return correctly formatted html response"
    if user_prompt is not None:
        if user_prompt != "":
            print(f"pr: {user_prompt}")
            base_prompt = base_prompt + user_prompt
    print('B111')
    chatmessages = [{"role":"system", "content":base_prompt}]
    #get generated article title
    chatmessages.append({"role":"user","content":f"Rewrite the article title {title} in KOREAN with h1 tag and it should be SEO friendly"})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    print('B222')
    chatmessages.append(output.choices[0].message)
    final_article = final_article + output.choices[0].message.content
    print('B333')
    regen_title = output.choices[0].message.content
    print("B4444")
    heading_image = ""
    if len(images) > 0:
        print(images[0])
        heading_image = gen_image_from_image("Regenrate this image in HQ 4K but it should not look exactly like this", images[0],stable_diff_key)
        print(heading_image)
        final_article = final_article + f"</br> <img src='{heading_image}'/> </br> </br>"
    print("B555")
    #get 5 headings considering the article text
    chatmessages.append({"role":"user","content":f"Considering this article text {text} return 5 sub headings for blog and make sure first one should be an introductory heading and response should be an array which can be parsed through json parsing for example ['Intro heading','heading2','heading3','heading4','heading5']"})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    print("B666")
    #considering it should be returning an array
    sub_headings_arrays = json.loads(output.choices[0].message.content)
    print("B777")
    count = 1
    for sub_heads in sub_headings_arrays:
        chatmessages.append({"role":"user","content":f"For the sub heading {sub_heads} write 3 very long and detailed paragraph in KOREAN and return response as valid html format"})
        output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
        chatmessages.append(output.choices[0].message)
        final_article = final_article + output.choices[0].message.content
        print("B888")
        if len(images) >= count + 1:
            #then there exist image for headings
            sub_heading_image = await gen_image_from_image("Regenerate this image in HQ 4K but it should not look exactly like this", images[count],stable_diff_key)
            if sub_heading_image is not None:
                final_article = final_article + f"</br> <img src='{sub_heading_image}'/> </br> </br>"
            count=count+1
    #generate conclusion 
    print("B999")
    chatmessages.append({"role":"user","content":f"Check this summary of the article: {summary} write a very long and detailed conclusion paragraph in KOREAN and return response as valid html format"})
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    chatmessages.append(output.choices[0].message)
    final_article = final_article + output.choices[0].message.content
    print("B101010")
    if len(images) > count:
        #then there exist image for conclusion
        sub_heading_image = gen_image_from_image("Regenerate this image in HQ 4K but it should not look exactly like this", images[count])
        if sub_heading_image is not None:
            final_article = final_article + f"</br> <img src='{sub_heading_image}'/> </br> </br>"
    print("B11910910")
    return {"article": final_article, "title": regen_title}

async def gen_image_from_image(prompt,image_url,key):
    print('gen images: ', image_url)
    url = "https://stablediffusionapi.com/api/v3/img2img"
    payload = json.dumps({
    "key": key,
    "prompt": prompt,
    "negative_prompt": None,
    "init_image": image_url,
    "width": "512",
    "height": "512",
    "samples": "1",
    "num_inference_steps": "30",
    "safety_checker": "no",
    "enhance_prompt": "yes",
    "guidance_scale": 7.5,
    "strength": 0.7,
    "seed": None,
    "webhook": None,
    "track_id": None
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.json())
    if response.json()['status'] == 'error':
        #skip image
        return None
    return response.json()['output'][0]