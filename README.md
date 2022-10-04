# MTG Draft Information

### Running:

This project utilizes flask and can be started by executing `flask run` in the project directory.

This command will start a web server and give a URL from which the functions of the project can be accessed.

### Account Management:

When the website is first loaded users will be given the option to login or register an account.

Once logged in, users have the option to logout or update their password by clicking the respective options in the page's header.

### Deck Management:

Once a user has logged in, they will be shown all of the decks that they have created.

Users with preexisting decks have the ability to view or delete any of those decks.

### Drafting:

Once logged in, a user also has the ability to start a draft by clicking `New Draft` in the page's header.

The user is then redirected to a page where they can choose set they would like to draft from.

##### Note:

*I have recommended a set that seems to work well. MTG's API functions differently based on the set and sometimes cards either will take a long time to load or will not load at all.*

A random pack of cards will then be displayed, from which the user can choose the card they would like in their deck.

In this fashion, the user the chooses from subsequently smaller and smaller sets of cards until the next set of cards would be empty.

Each pack *should* start with 14 cards and this process will happen three times resulting in a total of 42 cards.

After their 42nd choice, the user will be redirected to a page where they can view the cards that they chose.

### Viewing A Deck:

When a user views a deck, either by finishing a draft or choosing to do so from the main page, they are shown all of the cards in the deck.

In addition, they are given a list of basic lands, from the set which they drafted, that they can choose to add to their deck.

Upon adding lands, the page will be reloaded to reflect the changes made to the deck.

### Video:

[https://www.youtube.com/watch?v=GP4voCJg6Bk](https://www.youtube.com/watch?v=GP4voCJg6Bk)