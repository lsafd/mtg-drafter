# MTG Draft Design

### Starting Point:

Because I knew that I wanted to build a website in Flask, I started with my final code from CS50 Finance. After some alterations this allowed me to simply see that changes that I was making as I made them and made it much more simple for me to implement account features. I also made some stylistic changes (Like changing the favicon) just to give my project a slightly different look.

### SQL:

Because I already had a database with a table to store account information, I decided to make a table of decks linking each deck to a user's ID and the set the deck had been drafted from. This made it simple to find all the decks created by a specific user (As on the index page) and to add basic lands from the same set (As on the results page). I also created a table to store the all of the cards that had been chosen along with the ID of the deck they were a part of. This made it simple to find all of the cards in a specific deck (As on the results page).

### MTG's API:

I used Magic the Gathering's API for which there is a Python SDK. I use this API to list Magic the Gathering sets that can be drafted from, generate packs, find basic lands from a specific set, and associate names of cards with IDs.

However, this API is flawed (it seems that it has only ever been under sporadic development and has not seen any fundamental changes since 2019). Specifically, I had significant difficulties with generating packs. Among other problems, some sets generate packs without certain rarities of cards or with cards that have ID none. The first issue I could not fix as it would require that I essentially fully reimplement that function. However, I was able to fix the second error as the card's without IDs still have names which I use to search MTG's Gatherer and find card's the ID. However, this means that some sets will be much slower to load, as many requests have to be made to MTG's Gatherer, and sometimes the wrong art (As the request to Gatherer doesn't take into account the card's set) will be displayed ("Tenth Edition" is an example and should be the second option when choosing a set).

I have also limited the sets that can be chosen to those that are core, expansion, or masters sets, from which it should be possible to generate packs. There are a small number sets that still fail, but they mostly seem to be classification errors by MTG's API that I could only fix by checking every set and blacklisting those that fail ("Mystery Booster Retail Edition Foils" is an example of a set that seems to be misclassified as it is not a core, expansion, or masters set, but makes it past my filters).

### Index Overview:

The index page starts by querying my SQL database to create a list of the decks associated with the user who has logged in. This list, along with a variable indicating whether the list is empty, is passed to the template. If the list is empty the template puts "none" in the table of decks. Otherwise, the ID and set of each deck is listed in the table of decks and the user is given the options to view or remove a deck of their choice.

### Set Select Overview:

By clicking "New Draft" in the website's header after logging in, a user will be taken to set selection. This page queries MTG's API for all sets and then filters by the previously described specifications. This list is then passed to the template which lists all the sets as options.

### Draft Overview:

By choosing a set or picking a card while already on the draft page, a user will be taken to the draft page. If a user has a requested card to add to their deck, it is added to the SQL database associated with the users most recently created deck. If the user has chosen all 42 cards, they are sent, along with a list of the card IDs for the cards in the deck, a list of basic land IDs and names from the set, and the length of the basic land names list to the results template. Otherwise, this page finds the intended set using the set request or by looking at the set of the most recent deck created by the user. Then it queries MTG's API for a pack of cards from the given set. For each card in the pack, the name and ID are added to separate sets to be passed to the template. The template uses the IDs to display the card images and the names to display choices for the user.

### Results Overview:

By choosing to view a deck from the index page or adding a card to a deck they are viewing, a user will be taken to the results page. The results route functions similarly to the draft route when all 42 cards have been chosen in passing the same information to the template. The results template uses the IDs of the chosen cards to display images for all of the chosen cards. It used the names of the basic lands to display the choices of which basic lands to add and the IDs of those cards as the values for those options.

##### In Closing:

I hope that this is enough detail for my project to be evaluated. I wasn't exactly sure how much detail to include, so I left out parts in my explanation of routes and templates and didn't discuss the account related routes.
