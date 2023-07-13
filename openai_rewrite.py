import openai

openai.api_key = "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"

async def gpt_rewrite(title,text,summary):
    # re-write conent
    chatmessages = [{"role":"system", "content":"You should act as highly professional Korean blog writer and news reporter. You will be provided 3 things which are article title, article summary and article full text. You would rewrite a full blog post in reporter tone with 3rd person view and return correctly formatted HTML content using p,h1,h2,h4,strong,ul,li,ol html tags. It SHOULD BE OF ATLEAST 5000 WORDS  AND DO NOT GIVE EXPLANATION during rewriting"}, {"role":"user","content":f"article title: {title} , article summary: {summary}, article full text: {text}"}]
    output = await openai.ChatCompletion.acreate(model="gpt-4",messages=chatmessages)
    return output.choices[0].message.content