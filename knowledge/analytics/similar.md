Similarity Scores
The similarity scores were derived using a method similar (no pun intended) to the one used by Doug Drinen over at Pro-Football-Reference.com.
It is important to note that this method does not attempt to find players who were similar in style of play. Rather, it attempts to find players whose careers were similar in terms of quality and shape. By shape, I mean things like: How many years did he play? How good were his best years compared to his worst years? Did he have a few great years and then several mediocre years, or did he have many good-but-not-great years?
Another important item to note is that players are only compared to other players who played a comparable position. In other words, guards are compared to guards and guard-forwards; forwards are compared to forwards and forward-centers; and centers are compared to centers and center-forwards. This is not always perfect, but it works well enough absent more precise positional designations.
Players with at least three years played and a career value greater than zero (see #2 below) will have two similarity tables on their player pages. The first displays the most similar players through a given year (i.e., through year n). Only the first n years of a player's career are used when computing these scores. The second displays the most similar players based on entire careers. In this case, all years are used for all players.
Here is an example using Dirk Nowitzki and Larry Bird through 13 years:
- Get the Win Shares values for the first 13 years of
each player's career and order them from greatest to least.
DN 17.7 16.3 16.1 15.6 14.6 13.4 12.9 12.3 11.5 11.1 10.9 8.1 0.8 LB 15.8 15.7 15.2 15.0 14.0 13.6 12.5 11.2 10.8 9.5 6.6 5.5 0.5 
- Compute a career value for each player by
multiplying his best season by 1, his second-best season by 0.95, his
third-best season by 0.9, etc.
DN = 122.110 LB = 112.255 If either player has a career value less than zero then we stop here. Otherwise…
- Calculate the absolute difference in the Win Shares
values.
DN 17.7 16.3 16.1 15.6 14.6 13.4 12.9 12.3 11.5 11.1 10.9 8.1 0.8 LB 15.8 15.7 15.2 15.0 14.0 13.6 12.5 11.2 10.8 9.5 6.6 5.5 0.5 ---------------------------------------------------------------- 1.9 0.6 0.9 0.6 0.6 0.2 0.4 1.1 0.7 1.6 4.3 2.6 0.3
- Calculate the penalty by multiplying the first
penalty by 1, the second penalty by 0.95, the third penalty by 0.9, etc.
P = 10.155 
- Compute the similarity score as follows:
100 * (1 - (2 * 10.155 / (122.110 + 112.255))) = 91.3 
Through 13 years, the similarity between Nowitzki and Bird is 91.3 (with 100 being a perfect match). In this case, the career similarity score between Nowitzki and Bird is also 91.3, as both players have played 13 years through 2011-12. After Nowitzki's 14th season, another Win Shares value will be added to Nowitzki's row and a zero will be be added to Bird's row. The similarity scores will then be computed using the same method as outlined above.