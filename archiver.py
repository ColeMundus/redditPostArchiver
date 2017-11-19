#!/usr/bin/env python
# -*- coding: utf-8 -*-

import snudown
import datetime
import requests
import argparse
import time
import re
import os
import sys
from requests.exceptions import HTTPError
from pprint import pprint
from anytree import Node, RenderTree, LevelOrderIter
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument("post", help="The post ID number you would like to download")
parser.add_argument("-p", "--path", help="Output download path", default="submissions")
parser.add_argument("-c", "--css", help="Stylesheet path embeded in html", default="css/style.css")
args = parser.parse_args()
args.path = args.path.rstrip('/') + '/'
if not os.path.exists(args.path):
    os.makedirs(args.path)
outputFilePath = args.path + args.post + '.html'
monthsList = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def parsePost(post, postID):
    htmlFile.write('<!DOCTYPE html>\n<html>\n<head>\n\t<meta charset="utf-8"/>\n\t<link type="text/css" rel="stylesheet" href="' + args.css +'"/>\n\t<title>' + post['title'] + '</title>\n</head>\n<body>\n')
    try:
        postAuthor = post['author']
    except AttributeError:
    	postAuthor = '[Deleted]'
    htmlFile.write('<div class="title">\n')
    if post['is_self']:
        htmlFile.write(post['title'])
        htmlFile.write('\n<br/><strong>')
    else:
        htmlFile.write('<a id="postlink" href="' + post['url'])
        htmlFile.write('">')
        htmlFile.write(post['title'])
        htmlFile.write('</a>\n<br/><strong>')
    htmlFile.write('Posted by <a id="userlink" href="' + 'http://reddit.com/u/' + post['author'] + '">')
    htmlFile.write(postAuthor)
    htmlFile.write('</a>. </strong><em>')
    htmlFile.write('Posted at ')
    postDate = time.gmtime(post['created_utc'])
    htmlFile.write(str(postDate.tm_hour) + ':')
    htmlFile.write(str(postDate.tm_min) + ' UTC on ')
    htmlFile.write(monthsList[postDate.tm_mon-1] + ' ')
    htmlFile.write(str(postDate.tm_mday) + ', ' + str(postDate.tm_year))
    htmlFile.write('. ' + str(post['score']))
    if post['is_self']:
        htmlFile.write(' Points. </em><em>(self.<a id="selfLink" href="')
    else:
        htmlFile.write(' Points. </em><em>(<a id="selfLink" href="')
    htmlFile.write('http://reddit.com/r/' + post['subreddit'] + '">' + post['subreddit'])
    if post['is_self']:
        htmlFile.write('</a>)</em><em>')
    else:
        htmlFile.write('</a> Subreddit)</em><em>')
    htmlFile.write(' (<a id="postpermalink" href="' + post['permalink'] + '">Permalink</a>)</em>\n')
    if post['is_self']:
        htmlFile.write('<div class="post">\n')
        htmlFile.write(snudown.markdown(fixMarkdown(post['selftext'])))
        htmlFile.write('</div>\n')
    else:
        htmlFile.write('<div class="post">\n<p>\n')
        htmlFile.write(post['url'])
        htmlFile.write('</p>\n</div>\n')
    htmlFile.write('</div>\n')
    ids = requests.get('https://api.pushshift.io/reddit/submission/comment_ids/' + postID).json()['data']
    c = []
    for x in chunks(ids, 500):
        c += requests.get('https://api.pushshift.io/reddit/search/comment/?ids=' + ','.join(x)).json()['data']
    comments = {postID: Node(postID)}
    for x in c:
        try:
            comments[x['id']] = Node(x, parent=comments[x['parent_id'][3:]])
        except KeyError as e:
            print('--[ Failed to retrive comment {} ]--'.format(e.args[0]))
    for node in [node.name for node in LevelOrderIter(comments[postID], maxlevel=2)]:
        if node != postID:
            parseComment(node, postAuthor, comments)
    htmlFile.write('<hr id="footerhr">\n<div id="footer"><em>Archived on' + str(datetime.datetime.utcnow()) + 'UTC</em></div>\n\n</body>\n</html>\n')
def parseComment(comment, postAuthor, comments, isRoot=True):
    try:
        commentAuthorName = comment['author']
    except AttributeError:
        commentAuthorName = '[Deleted]'
    if isRoot:
        htmlFile.write('<div id="' + str(comment['id']) + '" class="comment">\n')
    else:
        htmlFile.write('<div id="' + str(comment['id']) + '" class="comment" style="margin-bottom:10px;margin-left:0px;">\n') 
    htmlFile.write('<div class="commentinfo">\n')
    if commentAuthorName != '[Deleted]':
        if postAuthor != '[Deleted]' and postAuthor == commentAuthorName:
            htmlFile.write('<a href="' + 'http://reddit.com/u/' + comment['author'])
            htmlFile.write('" class="postOP-comment">' + commentAuthorName + '</a> <em>')
        else:
            htmlFile.write('<a href="' + 'http://reddit.com/u/' + comment['author'])
            htmlFile.write('">' + commentAuthorName + '</a> <em>')
    else:
        htmlFile.write('<strong>[Deleted]</strong> <em>')
    try:
        htmlFile.write(str(comment['score']))
    except KeyError as e:
        htmlFile.write('1')
    htmlFile.write(' Points </em><em>Posted at ')
    postDate = time.gmtime(comment['created_utc'])
    htmlFile.write(str(postDate.tm_hour) + ':' + str(postDate.tm_min) + ' UTC on ' + monthsList[postDate.tm_mon-1] + ' ' + str(postDate.tm_mday) + ', ' + str(postDate.tm_year) + '</em></div>\n')
    htmlFile.write(snudown.markdown(fixMarkdown(comment['body'])))
    for reply in [node.name for node in LevelOrderIter(comments[comment['id']], maxlevel=2)]:
        if reply['id'] != comment['id']:
            parseComment(reply, postAuthor, comments, False)
    htmlFile.write('</div>\n')
def fixMarkdown(markdown):
    return re.sub('\&gt;', '>', str(markdown))

post = requests.get('https://api.pushshift.io/reddit/search/submission/?ids=' + args.post).json()['data'][0]
htmlFile = open(outputFilePath,'w')
parsePost(post, args.post)
htmlFile.close()
