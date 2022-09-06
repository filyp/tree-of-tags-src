import json
import requests

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# allVotes {
#   voteType
#   _id
# }
posts_query = """
{
  posts(input: {terms: {limit: %d, offset: %d}}) {
    results {
      _id
      title
      postedAt
      user {
        username
        displayName
        pageUrl
      }
			tagRelevance
      wordCount
      voteCount
      baseScore
      score
      commentCount
    }
  }  
}

"""

tags_query = """
{
  tags(input: {terms: {limit: %d, offset: %d}}) {
    results {
      createdAt
      name
      slug
      core
      suggestedAsFilter
      postCount
      userId
      adminOnly
      deleted
      needsReview
      reviewedByUserId
      wikiGrade
      wikiOnly
      contributionStats
      introSequenceId
      _id
    }
  }
}
"""

comments_query = """
{
  comments(input: {terms: {limit: %d, offset: %d}}){
    results {
      allVotes {
        voteType
        _id
      }
  	  parentCommentId
  	  postedAt
  	  author
  	  postId
  	  tagId
  	  userId
  	  pageUrlRelative
  	  answer
  	  parentAnswerId
  	  directChildrenCount
  	  lastSubthreadActivity
  	  wordCount
  	  _id
  	  voteCount
  	  baseScore
  	  score
  	}
  }
}
"""


forum_apis = {
    "ea": "https://forum.effectivealtruism.org/graphql",
    "lw": "https://www.lesswrong.com/graphql",
    "af": "https://www.alignmentforum.org/graphql",
}


def run_query(query, args, forum):
    url = forum_apis[forum]
    headers = {"User-Agent": "Tree of Tags"}
    full_query = query % args
    r = requests.post(url, json={"query": full_query}, headers=headers)
    # check for errors
    if r.status_code != 200:
        raise Exception(
            f"Query failed to run by returning code of {r.status_code}.\nurl: {url}\nheaders: {headers}\nquery: {full_query}"
        )
    data = json.loads(r.text)
    return data["data"]


def get_all_posts(forum="ea", chunk_size=4000):
    all_posts = dict()
    offset = 0
    skipped_posts_no_tags = 0
    while True:
        current_posts = run_query(posts_query, (chunk_size, offset), forum)
        current_posts = current_posts["posts"]["results"]
        offset += chunk_size

        if len(current_posts) == 0:
            break

        for post in current_posts:
            # skip posts with no tags
            if post["tagRelevance"] is None:
                skipped_posts_no_tags += 1
                continue
            all_posts[post["_id"]] = post

    logger.info(f"Skipped {skipped_posts_no_tags} posts with no tags")
    assert len(all_posts) > 2000

    return all_posts


def get_all_tags(forum="ea", chunk_size=1000):
    all_tags = dict()
    offset = 0
    while True:
        current_tags = run_query(tags_query, (chunk_size, offset), forum)
        current_tags = current_tags["tags"]["results"]
        offset += chunk_size

        if len(current_tags) == 0:
            break

        for tag in current_tags:
            all_tags[tag["_id"]] = tag

    assert len(all_tags) > 700
    return all_tags


def get_all_comments(forum="ea", chunk_size=4000):
    """
    Watch out, this query takes ~3 minutes
    """
    all_comments = dict()
    offset = 0
    while True:
        current_comments = run_query(comments_query, (chunk_size, offset), forum)
        current_comments = current_comments["comments"]["results"]
        offset += chunk_size

        if len(current_comments) == 0:
            break

        for comment in current_comments:
            all_comments[comment["_id"]] = comment
        # break

    assert len(all_comments) > 700
    return all_comments
