#!/usr/bin/env python
# -*- coding: utf-8 -*-

import praw
import snudown
import datetime
import requests
import time
import re
import sys
from requests.exceptions import HTTPError
from pprint import pprint
from anytree import Node, RenderTree, LevelOrderIter

# Default postID: #
postID='15zmjl'
# Path to which to output the file #
outputFilePath='./submissions/'
# The Path to the stylesheet, relative to where the html file will be stored #
css='css/style.css'

if len(sys.argv) == 1:
    print('No post ID was provided. Using default postID.')
elif len(sys.argv) > 2:
    print('Too Many Arguments. Using default postID.')
else:
    postID = sys.argv[1]
outputFilePath = outputFilePath + postID + '.html'
monthsList = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def writeHeader(title):
    htmlFile.write('<!DOCTYPE html>\n<html>\n<head>\n')
    htmlFile.write('\t<meta charset="utf-8"/>\n')
    htmlFile.write('\t<link type="text/css" rel="stylesheet" href="' + css +'"/>\n')
    htmlFile.write('\t<title>' + title + '</title>\n')
    htmlFile.write('</head>\n<body>\n')

def parsePost(post, postID):
    writeHeader(post['title'])
    postAuthorName = ''
    postAuthorExists = 0
    try:
        postAuthorName = post['author']
        postAuthorExists = 1
    except AttributeError:
    	postAuthorExists = 0
    htmlFile.write('<div class="title">\n')
    if post['is_self']:
        # The post is a self post
        htmlFile.write(post['title'])
        htmlFile.write('\n<br/><strong>')
    else:
        # The post is a link post
        htmlFile.write('<a id="postlink" href="' + post['url'])
        htmlFile.write('">')
        htmlFile.write(post['title'])
        htmlFile.write('</a>\n<br/><strong>')
    if postAuthorName:
        htmlFile.write('Posted by <a id="userlink" href="' + 'http://reddit.com/u/' + post['author'])
        htmlFile.write('">')
        htmlFile.write(postAuthorName)
        htmlFile.write('</a>. </strong><em>')
    else:
        htmlFile.write('Posted by [Deleted]. </strong><em>')
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
    htmlFile.write('http://reddit.com/r/' + post['subreddit'])
    htmlFile.write('">' + post['subreddit'])
    if post['is_self']:
        htmlFile.write('</a>)</em><em>')
    else:
        htmlFile.write('</a> Subreddit)</em><em>')
    htmlFile.write(' (<a id="postpermalink" href="')
    htmlFile.write(post['permalink'])
    htmlFile.write('">Permalink</a>)</em>\n')
    if post['is_self']:
        htmlFile.write('<div class="post">\n')
        htmlFile.write(snudown.markdown(fixMarkdown(post['selftext'])))
        htmlFile.write('</div>\n')
    else:
        htmlFile.write('<div class="post">\n<p>\n')
        htmlFile.write(post['url'])
        htmlFile.write('</p>\n</div>\n')
    htmlFile.write('</div>\n')
    c=requests.get('https://api.pushshift.io/reddit/search/comment/?ids=' + ','.join(requests.get('https://api.pushshift.io/reddit/submission/comment_ids/' + postID).json()['data'])).json()['data']
    comments = {postID: Node(postID)}
    for x in c:
        comments[x['id']] = Node(x, parent=comments[x['parent_id'][3:]])
    for node in [node.name for node in LevelOrderIter(comments[postID], maxlevel=2)]:
        if node != postID:
            parseComment(node, postAuthorName, postAuthorExists, comments)
    htmlFile.write('<hr id="footerhr">\n')
    htmlFile.write('<div id="footer"><em>Archived on ')
    htmlFile.write(str(datetime.datetime.utcnow()))
    htmlFile.write(' UTC</em></div>')
    htmlFile.write('\n\n</body>\n</html>\n')
    #Done
def parseComment(comment, postAuthorName, postAuthorExists, comments, isRoot=True):
    commentAuthorName = ''
    commentAuthorExists = 0
    try:
        commentAuthorName = comment['author']
        commentAuthorExists = 1
    except AttributeError:
        commentAuthorExists = 0
    if isRoot:
        htmlFile.write('<div id="' + str(comment['id']))
        htmlFile.write('" class="comment">\n')
    else:
        htmlFile.write('<div id="' + str(comment['id'])) 
        htmlFile.write('" class="comment" style="margin-bottom:10px;margin-left:0px;">\n')
    htmlFile.write('<div class="commentinfo">\n')
    if commentAuthorExists:
        if postAuthorExists and postAuthorName == commentAuthorName:
            htmlFile.write('<a href="' + 'http://reddit.com/u/' + comment['author'])
            htmlFile.write('" class="postOP-comment">' + commentAuthorName + '</a> <em>')
        else:
            htmlFile.write('<a href="' + 'http://reddit.com/u/' + comment['author'])
            htmlFile.write('">' + commentAuthorName + '</a> <em>')
    else:
        htmlFile.write('<strong>[Deleted]</strong> <em>')
    htmlFile.write(str(comment['score']))
    htmlFile.write(' Points </em><em>')
    htmlFile.write('Posted at ')
    postDate = time.gmtime(comment['created_utc'])
    htmlFile.write(str(postDate.tm_hour) + ':')
    htmlFile.write(str(postDate.tm_min) + ' UTC on ')
    htmlFile.write(monthsList[postDate.tm_mon-1] + ' ')
    htmlFile.write(str(postDate.tm_mday) + ', ' + str(postDate.tm_year))
    htmlFile.write('</em></div>\n')
    htmlFile.write(snudown.markdown(fixMarkdown(comment['body'])))
    for reply in [node.name for node in LevelOrderIter(comments[comment['id']], maxlevel=2)]:
        if reply['id'] != comment['id']:
            parseComment(reply, postAuthorName, postAuthorExists, comments, False)
    htmlFile.write('</div>\n')
    #Done
def fixMarkdown(markdown):
    return re.sub('\&gt;', '>', str(markdown))
try:
    post = requests.get('https://api.pushshift.io/reddit/search/submission/?ids=' + postID).json()['data'][0]
    htmlFile = open(outputFilePath,'w')
    parsePost(post, postID)
    htmlFile.close()
except HTTPError: 
    print('Unable to Archive Post: Invalid PostID or Log In Required (see line 157 of script)')
