# der_die_das

This is a small tool to practice German articles. To install it:

`git clone https://github.com/joost823/der_die_das`

`cd der_die_das`

To run it:

`python der_die_das.py`

Or

`python3 der_die_das.py`

If a wrong article is chosen, the relative probablity of the word being chosen again increases. Multiple wrong attemps increase the relative probability even more.

#### Settings

Add the `-r` argument to filter the dataset to a certain range range of word ids. Add `-r 100:200` to only play with words with ids between 100 and 200.

Add the `-p` option to filter the dataset to only play with at least a certain relative probabiliy, e.g. `-p 2`

Add the `-l` option to only play with words starting with a certain letter, e.g. `-l a`.
