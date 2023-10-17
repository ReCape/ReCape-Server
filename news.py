import os

def read_text(article):
    with open("news/" + article + "/text.txt", "r+") as file:
        text = file.read()
    return text

def get_news_articles(count = 0):
    articles = os.listdir("news")
    if count != 0 and count > len(articles):
        articles = articles[:count]
    
    compiled_articles = []

    for article in articles:
        compiled_articles.append(
            [article,
             read_text(article)])
    
    return compiled_articles

if __name__ == "__main__":
    get_news_articles(1)