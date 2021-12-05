# PowerTrip

## First Steps

Go to your [app preferences](https://www.reddit.com/prefs/apps). Click the "Create app" or "Create another app" button. Fill out the form like so:

name: My Example App  
App type: Choose the script option  
description: You can leave this blank  
about url: You can leave this blank  
redirect url: http://localhost  

Note: These examples will only work for script type apps, which will ONLY have access to accounts registered as "developers" of the app and require the application to know the user's password.

Hit the "create app" button. Make note of the client ID and client secret. For the rest of this page, it will be assumed that:  
Your username is: reddit_bot  
Your password is: snoo  
Your app's client ID is: p-jcoLKBynTLew  
Your app's client secret is: gko_LXELoV07ZBNUXrvWZfzE3aI  

Note: You should NEVER post your client secret (or your reddit password) in public. If you create a bot, you should take steps to ensure that the bot's password and the app's client secret are secured against digital theft.



`praw_username`

`praw_password`

`praw_client_id`

`praw_client_secret`

`praw_user_agent`

`pt_token`

`pt_queue_channel`
