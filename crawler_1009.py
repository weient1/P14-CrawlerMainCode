"""
 Created for CSC1009 Object Oriented Programming Assignment
 P02 Team 14 - NiceGroup
 This programs help to crawl data from Twitter and Reddit to retrieve post related to the different vaccines brand and do a analysis on the opinions and feelings of those posts 
 @author:Tan Wei En - 2609739T
         Aloysius Wong Jun Wei - 2609758W
         Huang JiaShu - 2609762H
         Gu JinMing - 2609772G
"""

# ---------- Libraries used ------------
#Tweepy is an API to crawls data from tweeter
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from tweepy import API
import tweepy
# json library to export json file 
import json 
from json import JSONDecodeError 
import pandas as pd #To use the dataFrame to store data and manipulate it
import csv #csv library needed as we will read and write txt files
import re #re library - regular expression is to cleanse the texts crawled
from textblob import TextBlob #API - polarity analysis sentiment
import os 
import time # time library to get current time at the start and end of the program - to show users how long it takes to run
import pydoc # documentation in this program
from datetime import datetime #to manipulate datetime 
import praw # this is Reddit API crawler

# ---------------- Authentications for the APIs ----------------
#Variables that contains the user credentials to access Twitter API 
access_token = "mytoken"
access_token_secret = "mytokenscret"
consumer_key = "consumerkey"
consumer_secret = "consumersecret"
        
# Authorization and Authentication - call the API 
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = API(auth, wait_on_rate_limit=True)

# Authorization and Authentication - to call the praw API
reddit = praw.Reddit(client_id='clientid',\
                     client_secret='secret_client_id',\
                     user_agent='applicationName',\
                     username='username',\
                     password='password')
    
def main():
    """ Main Function to call API and the scrap functions for the individual keywords  - this will run for 500 rounds with a 500seconds interval between each run.
        This would help to update the webpage with more accurate data from the latest tweets.
        - Users are allowed to enter their desired number of rounds and tweets that is to be crawled
    """
    try:
        noOfRounds = int(input("Enter number of rounds: ")) #store input in noOfRounds variable
        assert int(noOfRounds) > 0 and int(noOfRounds) <=100
    except AssertionError:
        raise AssertionError ("Entered an invalid number, please enter a number between 1 and 100")
    except ValueError:
        raise ValueError("You've entered a character, please enter a number")
    
    noOfCrawls = int(input("Enter number of tweets to be crawled for {} rounds: ".format(noOfRounds))) #print to ask user to enter the value
    noOfPost = noOftweets = noOfCrawls      
    vaccinesKeywords = ["moderna","pfizer","sputnik v","novavax","janssen","sinovac"] #Keywords to be search and crawl
    roundCount = 0 # int variable used as counter in the class

    
    twitterobjs = [Twitter(keyword,roundCount,noOftweets) for keyword in vaccinesKeywords] #Create twitter objectss with the differnt keywords in the vaccinesKeywords list (loop)
    redditobjs = [Reddit(keyword,roundCount,noOfPost) for keyword in vaccinesKeywords] #Create reddit objects with the differnt keywords in the vaccinesKeywords list (loop)


    for currentRound in range(noOfRounds): # Outer for-loop to run the numbers of time
        for objs in redditobjs: #for each reddit object in redditobjs
            objs.scrapreddit() #call to scrape post from reddit
        for objs in twitterobjs: #for each twitter object in twitterobjs
            objs.scraptweets() #call to scrape tweet
        if (currentRound+1 != noOfRounds): #if not the last round, it will rest for some time before running the next round - if shorter the sleep time, might not have much tweet that is tweeted by users
            print("\nProgram will wait for 500 Seconds before going on to run {}\n".format(currentRound+2))
            time.sleep(500) #wait for 500 seconds before going to the next run

class JSONEncoder(json.JSONEncoder):
    """
        This is to add dictionary named 'records' to the individual JSON files to make it neater
        Extend the JSON enconder so it will know how to serialise a dataframe 
        :param json.JSONEconder: this is to call the library
    """
    def default(self, obj):
        if hasattr(obj, 'to_json'): 
            return obj.to_json(orient='records') # make the object with an orient of 'records' <- will be the dictionary for the json file 
        return json.JSONEncoder.default(self, obj)   # return the extended JSON encoder

class Crawler():
    """
        Crawler() is the parent class Reddit and Twitter class, as some functions are shared between the 2 classes. It is better to store the similiar code in the parents class.
        :variable int twitterProg: A variable to tell the calling functions for which it is running for, twitter is set to 1
        "variable int redditProg: A variable to tell the calling function for which it is running for. Reddit is set to 2
    """
    #global public variable
    twitterProg = int(1)
    redditProg = int(0) 
    def __init__(self, keyword,roundCount):
        """
            To set the variables in the Crawler class
            :param string keyword: the keyword that is to be crawled
            :param int roundCount: the current round that is crawling
            :except AssertionError: When users entered a number that is NOT between 1 to 99 (for noOfRounds) 
            :except ValueError: if users enter something that is not numeric 
        """
        self._keyword = keyword
        self._roundCount = roundCount

            
    def increaseroundCount(self):
        """
            A numberofroundsleft function to increase the roundCount of the object -  which would be printed out to display in scraptweets() function
            
        """
        self._roundCount += 1
    
    def line_to_dict(self,split_Line,program):
        """ A line_to_dict function is to split each of the lines by ";" - Eg: username;singapore;2020-01-01 20:10:10;1;1;"textttttt"
            :param string split_line: is the individual lines from the txt file
            :return string array line_dict: An array that contains the splitted items - Eg: {username,singapore,2020-01-01 20:10:10,1,1,"texttttt"}
        """
        # Assumes that the first ';' in a line
        # is always the value separator
        line_dict = {} #create an empty array
        if (program == 1): # if program is 1 (twitter) 
            # keys (column name) to separate the lines in the txt file
            maxcol = int(9)
            keys = ["username","profilepic","location","tweetcreatedts","retweetcount","favouritecount","cleanselist","polarity","score"]
        else: # else - reddit (0)
            maxcol = int(7)
            keys = ["username","postscore", "num_comments", "datacreated","cleanselist","polarity","score"]

        i = 0 #int variable use as a counter 
        for part in split_Line: #split the lines
            if i == maxcol: #if i is 9 (max column) it will restart from 0 (username)
                i=0 
            line_dict[keys[i]] = part # add into the list
            i= i+1 # i+1 to increase the key position

        return line_dict #Return the array

    def polaritycheck(self,crawl_df):
        """
            A polaritycheck function to do a sentiment analysis to analyze the text to understand the opinion expressed by it.
            Typically, this sentiment returns with a positive or negative value, called polarity.
            In this function it will first do a further cleansing of data to remove unnecessary words, punctuation and emojis that could affect the polarity of the tweet.
            :param db_tweets: the dataFrame that stores the list of the crawled tweets
            :return db_tweets: the dataFrame that includes 2 new column - polarity and scores. if polarity < 0 : negative, else if polarity > 0 : postive, else neutral 
        """
        crawl_df["morecleanseText"] = crawl_df["cleanselist"] #duplicate the data in cleanselist column into a morecleanseText column in the dataFrame - db_tweets
        #Removing twitter handles, Punctuation - remove words that has no substance to aid in the sentiment analysis  (cause inaccruacy)
        removemention = lambda x: re.sub('@[\w]+',"",x) # This is to remove mentions in the tweet data - 
        removehashtag = lambda x: re.sub('#[\w]+',"",x) # This is to remove hashtags
        removelinks = lambda x: re.sub(r"https\S+","", x) # This is to remove links (picture links, web links etc)
        emoji_pattern = lambda x: re.sub(r"["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+","",x) # This is to remove emojis 

        punc = lambda x: re.sub(r'[?|$|.|!|"||ü|•|≥|¬|£|‚|Ä|ô|;|(|)|&]',"",x) #This is to remove characters and puntuation
        # Remove repetitions - eg: aaaaaaaaaaa -> return 'a'
        pattern = re.compile(r"(.)\1{2,}", re.DOTALL) 
        crawl_df["morecleanseText"] = crawl_df["morecleanseText"].str.replace(pattern, r"\1") # replace those repitition of those text in the morecleanseText column
        crawl_df["morecleanseText"] = crawl_df.morecleanseText.map(removemention).map(removelinks).map(punc).map(removehashtag).map(emoji_pattern) # Map those regex to the morecleanseText column
        crawl_df["morecleanseText"] = crawl_df.morecleanseText.str.lower() #make it all lower case
        # Create textblob objects of the tweets
        sentiment_objects = [TextBlob(tweet) for tweet in crawl_df["morecleanseText"]] # Run each text with the TextBlob function (API) - this will first break up the words into arrays
        #This will then calculate the polarity of text for each row nd store it in a temp list (sentiment_values under 0 column
        #a, and based on the polarity it will return the score. Eg: if polarity < 0 : negative, else if polarity > 0 : positive, else : neutral stored in the 1 column of the array
        sentiment_values = [[round(tweet.sentiment.polarity,3), "negative" if tweet.sentiment.polarity < 0 else "positive" if tweet.sentiment.polarity > 0 else "neutral"  ] for tweet in sentiment_objects]
        #This will create a dataFrame (sentiment_df) - with 2 columns "polarity" and "score". It will be concatenate to the main db_tweets dataFrame
        sentiment_df = pd.DataFrame(sentiment_values, columns=["polarity","score"])
        crawl_df = pd.concat([crawl_df, sentiment_df], axis=1) #concatenate the original db_tweets with sentiment_df - same index but add as column 
        return crawl_df #return the newly concat db_tweets back 

    def txt_to_json(self,filename,existingfile,program):
        """ A txt_to_json function to convert .txt files to .json file 
            :param string filename: the keyword that is to name the file
            :param string existingfile: is the name of the existing file that will be open
        """

        outfile = open(existingfile, encoding='utf-8', errors="ignore") #Open the existing file
        
        content = outfile.read() #store it in content variable
        outfile.close() #close the file if not might cause error during the next read
        splitcontent = content.splitlines()  #split the lines 
        # Split each line by pipe
        lines = [line.split(';') for line in splitcontent[1:]] #for each line in split content, split the data by the delimeter ';'

        # Convert each line to dict
        lines = [self.line_to_dict(l,program) for l in lines]
        if(program == 1):
            jsonfilename = filename+"_twitter_updated.json"
        else:
            jsonfilename = filename+"_reddit_updated.json"
            
        # Output JSON - filename - is the keyword
        with open(jsonfilename, 'w',encoding='utf-8') as fout:
            json.dump({'records':lines}, fout, indent=4,ensure_ascii=False,cls=JSONEncoder) #ensure_ascii -> will return the emojis and characters as it is 
        
        
    def cleanseList(self,crawl_df):
        """ A cleanseList function to cleanse the text obtain from the social media to remove unnecessary text - such as breaks and spaces 
            :param dataFrame db_tweet: is the dataFrame that stores the list of the crawled tweets
            :return db_tweets: the dataFrame that includes a new column to store the cleanse tweet (cleanselist)
        """
        crawl_df["cleanselist"] = crawl_df["text"] # Create a new col in db_tweets and duplicate the text from the text col into it
        #Removing breaks end enters - if not when transferring to json might cause error
        removeenter = lambda x: re.sub('\n',"",x) #remove enters (\n)
        removebreaks = lambda x: re.sub('\t',"", x) #remove breaks (\t)
        removebackslash = lambda x: re.sub(r'[\\]',"",x) #remove backslash
        removesemicol = lambda x: re.sub(r'[;]',"",x) #remove ; -> this will eventually cause error in json position as our txt file is split based on ';' delimeter
        # apply the re into the text in the cleanselist column in db_tweet    
        crawl_df["cleanselist"] = crawl_df.cleanselist.map(removeenter).map(removebreaks).map(removebackslash).map(removesemicol)
        return crawl_df #return the db_tweets

class Reddit(Crawler):
    """
        Reddit class is a child class from Crawler class - it runs and obtain data that was crawled from reddit using praw API

    """
    def __init__(self, keyword,roundCount, noOfPost):
        """
            To set the attributes of the Reddit class
            :param string keyword: keyword that is to be search on twitter crawler - inherited from Crawler
            :param int roundCount: is the number of round  - inherited from Crawler
            :param int noOfPost: number of posts to crawl per run
            :except AssertionError: When users entered a number that is NOT between 1 to 1000
            :except ValueError: if users enter something that is not numeric 
        """
        super().__init__(keyword,roundCount)
        try: #Try to see if user's input on noOfPost is valid
            assert int(noOfPost) > int(0) and int(noOfPost) <= int(1000) #to test if it is true that noOfPost entered by users is between 1 and 1000 if not between - will have an AssertionError else proceed
        except AssertionError : #If users entered a number that is too large or too small - it will print this error message and prompt the users to re-enter their choice
            raise AssertionError("Number entered is invalid, please consider another number that is between 1 to 1000")#print error message to display to users what error is it
        except TypeError:#if users enter an invalid character or alphabet it will cause a ValueError which will print this message and prompt the users to re-enter their choice
            raise TypeError("Please enter a valid number")#print error message to display to users what error is it
        else:
            self.__noOfPost = noOfPost

    def scrapreddit(self):
        """
            A scrapreddit function to crawl tweets from reddit, obtaining 5 kinds of data such as - id, post score, number of comments, date of the post created. At the end of each run, it will export out 2 files - .json and .txt containing the data that was crawled.
            A display message will be printed out after every run which also shows the time it takes to run.
            :exception FileNotFoundException: if program is run the first time, a new txt file will be created
        """
        self.increaseroundCount() #Increase roundCount at every round - to be display later
        posts = [] #Empty array, post to store crawled data
        nopost = 0 #nopost is a counter, which will display the number of post that is crawled
        # Calculate the time it takes to scrape tweets for each run:
        program_start = time.time() 
        start_run = time.time()
        keyword_subreddit = reddit.subreddit('all') #This will get from the reddit forum r/all - 
        for post in keyword_subreddit.search(self._keyword,limit=int(self.__noOfPost)): # Search the keyword in the subreddit, limit is the number of post that will be loop through
            if not post.stickied and post.is_self: #this is to check if the self.text is empty, we will obmit it cause not helpful to our polarity analysis
                datecreated = str(datetime.fromtimestamp(post.created)) #post.created will return a non-user readable datetime, thus will have to use datetime library to make it readable
                datecreated = datecreated[:datecreated.index(" ")] # We do this to remove the timestamp from the string as we only need the date
                posts.append([post.id, post.score, post.num_comments, post.selftext,datecreated ]) #append all the data we need into posts
                nopost +=1 # nopost + 1 when appended something

        # Run ended:
        print('no. of tweets scraped for {} in run {} is {}'.format(self._keyword, self._roundCount, nopost)) #print to inform users    
        posts_df = pd.DataFrame(posts,columns=['id', 'postscore', 'num_comments', 'text', 'datecreated']) # created dataframe to store the crawled data
        posts_df = self.cleanseList(posts_df) #cleanse the text
        posts_df = self.polaritycheck(posts_df) #do polarity analysis of the text
        posts_df.drop(['text', 'morecleanseText'], axis=1, inplace=True) #drop 'text' column -> save space & time since it is the same as cleanselist

        existingfile = self._keyword + '_full_reddit_list.txt' #file name to be created to store the data
        data = data2 = "" #empty string to store the text in txt file
        try:#already have existing txt file
            outf = open(existingfile,"r")
        except FileNotFoundError: # Create new one (txt & json) - if no existing file (first time running the program)
            print("File does not exist, a new file will be created . . . . .")
            posts_df.to_csv(existingfile, encoding='utf-8', index = False, sep=';')
            # Output JSON 
            self.txt_to_json(self._keyword,existingfile,self.redditProg)
        else: # else if have existing file already it will run here, like update the existing list with current + existing 
            posts_df.to_csv(self._keyword+"_current_reddit_list.txt", index = False, sep=';',header=False)
            
            # Reading data from file1 - no need to fp.close() because using with open() will automatically close after the function finish running
            with open(existingfile, encoding='utf-8', errors="ignore") as fp: 
                data = fp.read() #Read lines from (keyword)_full_tweet_list.txt - all the existing data 
            # Reading data from file2 - no need to fp.close() because using with open() will automatically close after the function finish running
            with open(self._keyword+"_current_reddit_list.txt", encoding='utf-8',errors="ignore") as fp: 
                data2 = fp.read() #Read lines from (keyword)_current_tweet_list.txt - data from current run
            # Merging 2 files - To add the data of file2 
            data += data2 
            #Export the merged txt file to json, first open the _full_tweet_list.txt file - no need to fp.close() because using with open() will automatically close after the function finish running
            with open (existingfile, encoding='utf-8',mode='w') as fp: 
                fp.write(data) 
            self.txt_to_json(self._keyword,existingfile,self.redditProg) #call the function to export into json file
            os.remove(self._keyword+"_current_reddit_list.txt") #remove the temporary .txt file (only store the current txt for each run)
        program_end = time.time() #get current time
        print('\t Reddit Scraping has completed!') #display to user that current run is completed
        print('Total time taken to scrap is {0:.3f} minutes.\n'.format(round(program_end - program_start)/60, 2)) #calculate the diff between start and end time and display      

        
class Twitter(Crawler):
    """
        Twitter class is a child class from Crawler class - it runs and obtain data that was crawled from twitter using Tweepy API


    """
    
    def __init__(self,keyword,roundCount,noOftweets):

        super().__init__(keyword,roundCount) #From Crawler - since Twitter class is inherited from Crawler
        try:
            assert int(noOftweets) > int(0) and int(noOftweets) <= int(1000) #to test if it is true that noOfCrawls entered by users is between 1 and 1000 if not between - will have an AssertionError else proceed
        except AssertionError : #If users entered a number that is too large or too small - it will print this error message and prompt the users to re-enter their choice
            raise AssertionError("Number entered is invalid, please consider another number that is between 1 to 1000")#print error message to display to users what error is it
        except TypeError:#if users enter an invalid character or alphabet it will cause a ValueError which will print this message and prompt the users to re-enter their choice
            raise TypeError("Please enter a valid number")#print error message to display to users what error is it
        else: # if valid, it will then initialise 
            self.__noOftweets = noOftweets  
 

    def scraptweets(self):
        """ 
            A scraptweets function to crawl tweets from twitter, obtaining 5 kinds of data such as - username, profile picture link, location, date of the tweet created, number of retweet counts, number of favourite counts and the tweet text itself. At the end of each run, it will export out 2 files - .json and .txt containing the data that was crawled. A display message will be printed out after every run which also shows the time it takes to run.
            :exception FileNotFoundException: if program is run the first time, a new txt file will be created
            :exception : favouritecount, if tweet.retweeted_status.favourite_count does not exist, it will take results from tweet.favourite_count
        """
    
        # Define a for-loop to generate tweets at regular intervals
        # We cannot make large API call in one go. So need go multiple rounds
        self.increaseroundCount() #increase roundCount at every round- to be display later 
        # Define a pandas dataframe to store the date:
        db_tweets = pd.DataFrame(columns = ['username', 'profilepic','location',  'tweetcreatedts',
                                            'retweetcount',"favouritecount", 'text'])
        program_start = time.time()
        # Calculate the time it takes to scrape tweets for each run:
        start_run = time.time()

        # Collect tweets using the Cursor object
        # .Cursor() returns an object that you can iterate or loop over to access the data collected.
        # Each item in the iterator has various attributes that you can access to get information about each tweet
        # we do not want to include retweets because it will be repetitive so added a filter:retweets. tweet_mode = 'extended' to get full_tweets (last time only 140 character max now is 240).
        # we only want to read tweets that is in eng -> lang="en"
        tweets = tweepy.Cursor(api.search, q=self._keyword+'-filter:retweets', lang="en",since="2021-01-01", tweet_mode='extended').items(self.__noOftweets)
        # Store these tweets into a python list
        tweet_list = [tweet for tweet in tweets]
        # Obtain the following info:
            # user.screen_name - twitter handle
            # user.profile_image_url - user's profile picture (link)
            # user.location - where is he tweeting from
            # created_at - when the tweet was created
            # retweet_count - no. of retweets
            # retweeted_status.full_text - full text of the tweet
        # Begin scraping the tweets individually:
        noTweets = 0
        for tweet in tweet_list:
        # Pull the values
                username = tweet.user.screen_name
                profilepic = tweet.user.profile_image_url
                location = tweet.user.location
                tweetcreatedts = str(tweet.created_at)
                tweetcreatedts = tweetcreatedts[:tweetcreatedts.index(" ")]

                retweetcount = tweet.retweet_count
                try:
                    favouritecount = tweet.retweeted_status.favorite_count
                except:
                    favouritecount = tweet.favorite_count
                text = tweet.full_text
        # Add the 7 variables to the empty list - ith_tweet:
                ith_tweet = [username, profilepic, location, tweetcreatedts, retweetcount,favouritecount, text]
        # Append to dataframe - db_tweets
                db_tweets.loc[len(db_tweets)] = ith_tweet
        # increase counter - noTweets  
                noTweets += 1
  
        db_tweets = self.cleanseList(db_tweets) #cleanse the dataFrame - since some tweets contains breaks and spaces which could affect the exporting of json
        db_tweets = self.polaritycheck(db_tweets) #call polaritycheck function

        db_tweets.drop(['text', 'morecleanseText'], axis=1, inplace=True) #drop 'text' column -> save space & time since it is the same as cleanselist
        
        # Run ended:
        print('no. of tweets scraped for {} in run {} is {}'.format(self._keyword, self._roundCount, noTweets)) #print to inform users
        #this will be used to store the txt file name
        existingfile = self._keyword + '_full_tweet_list.txt' 
    
        try: #already have existing txt file
            outf = open(existingfile, "r") #try to open (keyword)_full_tweet_list.txt
        except FileNotFoundError: # Create new one (txt & json) - if no existing file (first time running the program)
            print("File does not exist, a new file will be created . . . . .")
            db_tweets.to_csv(existingfile, encoding='utf-8', index = False, sep=';')
            # Output JSON 
            self.txt_to_json(self._keyword,existingfile,self.twitterProg)
        else: # else if have existing file already it will run here, like update the existing list with current + existing 
            db_tweets.to_csv(self._keyword+"_current_tweet_list.txt", index = False, sep=';',header=False)
            data = data2 = "" 
            
            # Reading data from file1 - no need to fp.close() because using with open() will automatically close after the function finish running
            with open(existingfile, encoding='utf-8', errors="ignore") as fp: 
                data = fp.read() #Read lines from (keyword)_full_tweet_list.txt - all the existing data 
            # Reading data from file2 - no need to fp.close() because using with open() will automatically close after the function finish running
            with open(self._keyword+"_current_tweet_list.txt", encoding='utf-8',errors="ignore") as fp: 
                data2 = fp.read() #Read lines from (keyword)_current_tweet_list.txt - data from current run
            # Merging 2 files - To add the data of file2 
            data += data2 
            #Export the merged txt file to json, first open the _full_tweet_list.txt file - no need to fp.close() because using with open() will automatically close after the function finish running
            with open (existingfile, encoding='utf-8',mode='w') as fp: 
                fp.write(data) 
            self.txt_to_json(self._keyword,existingfile,self.twitterProg) #call the function to export into json file
            os.remove(self._keyword+"_current_tweet_list.txt") #remove the temporary .txt file (only store the current txt for each run)
        program_end = time.time() #get current time
        print('\t Twitter Scraping has completed!') #display to user that current run is completed
        print('Total time taken to scrap is {0:.3f} minutes.\n'.format(round(program_end - program_start)/60, 2)) #calculate the diff between start and end time and display


if __name__ == "__main__":
    print(" - - - Crawler Program - - -")
    print("Step 1: Enter the number of rounds and number of tweets and posts to be crawled ")
    print("Step 2: Wait for the program to run, a .json and .txt file will be exported to the folder of this program")
    print("Step 3: If you entered multiple runs, the program will have a 500 seconds interval between each round")
    print("\n")
    main() #call main function

    
    
    print("-- Twitter Crawl Completed --")
