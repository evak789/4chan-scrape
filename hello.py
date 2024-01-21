import requests

# download the front page of the "pol" channel
URL = "https://boards.4chan.org/pol/"
page = requests.get(URL)

# save it to an .html file
fp = open("pol.html", "w")
fp.write(page.text)
fp.close()
# print(page.text)

