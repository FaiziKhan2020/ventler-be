# Natural Language Toolkit, visit: https://www.nltk.org/
import nltk

from newspaper import Article

def fetchArtcile(fetchUrl):
    url = fetchUrl
    article = Article(url)

    article.download()
    article.parse()
    nltk.download('punkt')
    article.nlp()
    article.config.keep_article_html = True

    return article