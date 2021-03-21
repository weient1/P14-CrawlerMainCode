
import unittest
from crawler_1009 import *
from unittest.mock import patch
from unittest import TestCase


class unittestcases(unittest.TestCase):

    def test_Twitter_noOftweets_negative(self): #Test when input of noOftweets is negative
        with self.assertRaises(AssertionError): #if it will correctly raise AssertionError
            twitterobj = Twitter("moderna",10,-1000)
    def test_Twitter_noOftweets_largeinput(self): #Test when input of noOftweets is too large
        with self.assertRaises(AssertionError): #if it will correctly raise AssertionError
            twitterobj = Twitter("moderna",10,100000000)
    def test_Twitter_noOfRounds_character(self): #Test when input of noOftweets is not a numeric value
        with self.assertRaises(ValueError): #if it will correctly raise ValueError
            twitterobj = Twitter("moderna",1,"testttttt")

    def test_Reddit_noOfPost_negative(self): #Test when input of noOfPost is negative
        with self.assertRaises(AssertionError): #if it will correctly raise AssertionError
            redditobj = Reddit("moderna",10,-1000)
    def test_Reddit_noOfPost_largeinput(self):
        with self.assertRaises(AssertionError): #Test when input of noOfPost is too large
            redditobj = Reddit("moderna",10,100000000) #if it will correctly raise Value Error
    def test_Reddit_noOfPost_character(self): #Test when input of noOfPost is not a numeric value
        with self.assertRaises(ValueError): #raise ValueError
            redditobj = Reddit("moderna",1,"testttttt")

    def test_Twiiter_get_increaseroundCount(self): #Test if the function increaseroundCount works correctly
        noOfRounds = 2 #number of rounds users want
        twitterobj = Twitter("moderna",0,1) # create an object with roundCount as 0
        for i in range(noOfRounds): # Run scraptweet 2 times - every run it will increase roundCount by 1
            twitterobj.scraptweets()
        self.assertEqual(twitterobj._roundCount, noOfRounds) #test if it is equal 


    def test_noOfRounds_negative_input(self): #This is to check noOfRound input is negative or not (in main())
        with self.assertRaises(AssertionError): #test if will raise AssertionError
            with patch('builtins.input', return_value=-1),\ #create mock input
                 patch('builtins.print') as new_print:
                main() #run in main()

    def test_noOfRounds_largeinput_input(self): #Check noOfRound input is it too large in main()
        with self.assertRaises(AssertionError): #test if will raise AssertionError
            with patch('builtins.input', return_value=-1000000),\ #create mock input
                 patch('builtins.print') as new_print:
                main() #run in main()                       

    def test_noOfRounds_character_input(self): #Check noOfRound input is it not a numeric value 
        with self.assertRaises(ValueError): #test if will raise ValueError
            with patch('builtins.input', return_value='hello'),\ #create mock input
                 patch('builtins.print') as new_print:
                main()  #run in main()          


if __name__ == '__main__':
    unittest.main()
