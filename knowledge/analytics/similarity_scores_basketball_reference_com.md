Similarity Scores | Basketball-Reference.com



* [Sports Reference ®](https://www.sports-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* [Baseball](https://www.baseball-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* [Football](https://www.pro-football-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav) [(college)](https://www.sports-reference.com/cfb/)
* [Basketball](https://www.basketball-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav) [(college)](https://www.sports-reference.com/cbb/)
* [Hockey](https://www.hockey-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* [Soccer](https://fbref.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* [Blog](https://www.sports-reference.com/blog/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* [Stathead ®](https://www.sports-reference.com/stathead/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* [Immaculate Grid ®](https://www.sports-reference.com/immaculate-grid/basketball/mens/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* [Questions or Comments?](https://www.sports-reference.com/feedback/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav)
* Welcome  · [Your Account](https://www.sports-reference.com/profile/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_account)
* [Logout](https://www.sports-reference.com/users/logout.cgi)
* [Ad-Free Login](https://www.sports-reference.com/users/login.cgi?token=1)
* [Create Account](https://www.sports-reference.com/stathead/signup.cgi)

[![Basketball-Reference.com ](https://cdn.ssref.net/req/202606251/logos/bbr-logo.svg)](/)

[MENU](#site_menu_link)

* [Players](/players/)
* [Teams](/teams/)
* [Seasons](/leagues/)
* [Leaders](/leaders/)
* [Scores](/boxscores/)
* [WNBA](/wnba/)
* [Draft](/draft/)
* [Stathead](https://www.sports-reference.com/stathead/sport/basketball/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_topnav_stathead&utm_content=lnk_top)
* [Newsletter](https://www.basketball-reference.com/email/)
* [Full Site Menu Below](#site_menu_link)

You are here:

[BBR Home Page](/)  > [About](/about/)  > **Similarity Scores**

* Welcome  · [Your Account](https://www.sports-reference.com/profile/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_account)
* [Logout](https://www.sports-reference.com/users/logout.cgi)
* [Ad-Free Login](https://www.sports-reference.com/users/login.cgi?token=1)
* [Create Account](https://www.sports-reference.com/stathead/signup.cgi)



**About** Menu

* [About Basketball Reference](/about/)

**Keyboard Shortcuts**

\ to toggle sidebar navigation

/ to toggle search input

[More about this update](https://www.sports-reference.com/blog/2025/11/in-page-navigation-redesign-on-basketball-reference/)

# Similarity Scores

The similarity scores were derived using a [method](https://www.pro-football-reference.com/about/approximate_value.htm#:~:text=Similar%20Players%20by%20AV)
similar (no pun intended) to the one used by Doug Drinen over at
Pro-Football-Reference.com.

It is important to note that this method does not attempt to find players
who were similar in style of play. Rather, it attempts to find players
whose careers were similar in terms of quality and shape. By shape, I mean
things like: How many years did he play? How good were his best years
compared to his worst years? Did he have a few great years and then
several mediocre years, or did he have many good-but-not-great years?

Another important item to note is that players are only compared to other
players who played a comparable position. In other words, guards are
compared to guards and guard-forwards; forwards are compared to forwards
and forward-centers; and centers are compared to centers and
center-forwards. This is not always perfect, but it works well enough
absent more precise positional designations.

Players with at least three years played and a career value greater than zero (see #2
below) will have two similarity tables on their player pages. The first
displays the most similar players through a given year (i.e., through year
n). Only the first n years of a player's career are used when
computing these scores. The second displays the most similar players
based on entire careers. In this case, all years are used for all
players.

Here is an example using [Dirk
Nowitzki](/players/n/nowitdi01.html) and [Larry Bird](/players/b/birdla01.html) through
13 years:

1. Get the Win Shares values for the first 13 years of
   each player's career and order them from greatest to least.

   ```
   DN 17.7 16.3 16.1 15.6 14.6 13.4 12.9 12.3 11.5 11.1 10.9  8.1  0.8 
   LB 15.8 15.7 15.2 15.0 14.0 13.6 12.5 11.2 10.8  9.5  6.6  5.5  0.5
   ```
2. Compute a career value for each player by
   multiplying his best season by 1, his second-best season by 0.95, his
   third-best season by 0.9, etc.

   ```
   DN = 122.110
   LB = 112.255
   ```

   If either player has a career value less than zero then we stop here.
   Otherwise…
3. Calculate the absolute difference in the Win Shares
   values.

   ```
   DN 17.7 16.3 16.1 15.6 14.6 13.4 12.9 12.3 11.5 11.1 10.9  8.1  0.8 
   LB 15.8 15.7 15.2 15.0 14.0 13.6 12.5 11.2 10.8  9.5  6.6  5.5  0.5
      ----------------------------------------------------------------
       1.9  0.6  0.9  0.6  0.6  0.2  0.4  1.1  0.7  1.6  4.3  2.6  0.3
   ```
4. Calculate the penalty by multiplying the first
   penalty by 1, the second penalty by 0.95, the third penalty by 0.9, etc.

   ```
   P = 10.155
   ```
5. Compute the similarity score as follows:

   ```
   100 * (1 - (2 * 10.155 / (122.110 + 112.255))) = 91.3
   ```

Through 13 years, the similarity between Nowitzki and Bird is 91.3 (with
100 being a perfect match). In this case, the career similarity score
between Nowitzki and Bird is also 91.3, as both players have played 13
years through 2011-12. After Nowitzki's 14th season, another Win Shares
value will be added to Nowitzki's row and a zero will be be added to
Bird's row. The similarity scores will then be computed using the same
method as outlined above.

* Welcome  · [Your Account](https://www.sports-reference.com/profile/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_account)
* [Logout](https://www.sports-reference.com/users/logout.cgi)
* [Ad-Free Login](https://www.sports-reference.com/users/login.cgi?token=1)
* [Create Account](https://www.sports-reference.com/stathead/signup.cgi)

You are here: [BBR Home Page](/)  > [About](/about/)  > **Similarity Scores**

## Full Site Menu

* [Return to Top](#header)

* [Players](/players/)

  **In the News**:
  [V. Wembanyama](/players/w/wembavi01.html "Victor Wembanyama"),
  [L. James](/players/j/jamesle01.html "LeBron James"),
  [K. Durant](/players/d/duranke01.html "Kevin Durant"),
  [J. Embiid](/players/e/embiijo01.html "Joel Embiid"),
  [J. Harden](/players/h/hardeja01.html "James Harden"),
  [S. Curry](/players/c/curryst01.html "Stephen Curry"),
  [L. DonÄiÄ](/players/d/doncilu01.html "Luka DonÄiÄ")

  [...](/players/)

  **All-Time Greats**:
  [E. Hayes](/players/h/hayesel01.html "Elvin Hayes"),
  [J. Stockton](/players/s/stockjo01.html "John Stockton"),
  [H. Olajuwon](/players/o/olajuha01.html "Hakeem Olajuwon"),
  [W. Chamberlain](/players/c/chambwi01.html "Wilt Chamberlain"),
  [D. Schayes](/players/s/schaydo01.html "Dolph Schayes"),
  [J. Havlicek](/players/h/havlijo01.html "John Havlicek")

  [...](/players/)

  **Active Greats**:
  [L. James](/players/j/jamesle01.html "LeBron James"),
  [G. Antetokounmpo](/players/a/antetgi01.html "Giannis Antetokounmpo"),
  [N. JokiÄ](/players/j/jokicni01.html "Nikola JokiÄ"),
  [J. Harden](/players/h/hardeja01.html "James Harden"),
  [S. Curry](/players/c/curryst01.html "Stephen Curry"),
  [K. Durant](/players/d/duranke01.html "Kevin Durant")

  [...](/players/)
* [Teams](/teams/)


  **Atlantic**:
  [Toronto](/teams/TOR/2027.html),
  [Boston](/teams/BOS/2027.html),
  [New York](/teams/NYK/2027.html),
  [Brooklyn](/teams/BRK/2027.html),
  [Philadelphia](/teams/PHI/2027.html)

  **Central**:
  [Cleveland](/teams/CLE/2027.html),
  [Indiana](/teams/IND/2027.html),
  [Detroit](/teams/DET/2027.html),
  [Chicago](/teams/CHI/2027.html),
  [Milwaukee](/teams/MIL/2027.html)

  **Southeast**:
  [Miami](/teams/MIA/2027.html),
  [Atlanta](/teams/ATL/2027.html),
  [Charlotte](/teams/CHO/2027.html),
  [Washington](/teams/WAS/2027.html),
  [Orlando](/teams/ORL/2027.html)

  **Northwest**:
  [Oklahoma City](/teams/OKC/2027.html),
  [Portland](/teams/POR/2027.html),
  [Utah](/teams/UTA/2027.html),
  [Denver](/teams/DEN/2027.html),
  [Minnesota](/teams/MIN/2027.html)

  **Pacific**:
  [Golden State](/teams/GSW/2027.html),
  [Los Angeles Clippers](/teams/LAC/2027.html),
  [Sacramento](/teams/SAC/2027.html),
  [Phoenix](/teams/PHO/2027.html),
  [Los Angeles Lakers](/teams/LAL/2027.html)

  **Southwest**:
  [San Antonio](/teams/SAS/2027.html),
  [Dallas](/teams/DAL/2027.html),
  [Memphis](/teams/MEM/2027.html),
  [Houston](/teams/HOU/2027.html),
  [New Orleans](/teams/NOP/2027.html)
* [Seasons](/leagues/)

  [2025-26](/leagues/NBA_2026.html),
  [2024-25](/leagues/NBA_2025.html),
  [2023-24](/leagues/NBA_2024.html),
  [2022-23](/leagues/NBA_2023.html),
  [2021-22](/leagues/NBA_2022.html),
  [2020-21](/leagues/NBA_2021.html),
  [2019-20](/leagues/NBA_2020.html)
  ...
* [Leaders](/leaders/)

  [Season Points](/leaders/pts_season.html),
  [Career Rebounds](/leaders/trb_career.html),
  [Active Assists](/leaders/ast_active.html),
  [Yearly Steals](/leaders/stl_yearly.html),
  [Progressive Blocks](/leaders/blk_progress.html)
  ...

  Or, view ["Trailers"](/trailers/) for [Season Field Goal Pct](/trailers/fg_pct_season.html), or [Career Blocks Per Game](/trailers/blk_per_g_career.html)
* [NBA Scores](/boxscores/)

  [Yesterday's Games](/boxscores/) and [Scores from any date in BAA/NBA or ABA history](/boxscores/)
* [NBA Schedules](/leagues/NBA_2026_games.html)

  [Team Schedules](/teams/BOS/2026_games.html) and [League Schedules](/leagues/NBA_2026_games.html)
* [NBA Standings](/leagues/NBA_2026_standings.html)

  [Today's Standings](/leagues/NBA_2026_standings.html) and [Standings for any date in history](/friv/standings.fcgi)
* [Stathead](https://www.sports-reference.com/stathead/basketball/?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead)

  **Player Finders**:
  [Season Finder](https://www.sports-reference.com/stathead/basketball/player-season-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Game Finder](https://www.sports-reference.com/stathead/basketball/player-game-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Streak Finder](https://www.sports-reference.com/stathead/basketball/player-streak-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Span Finder](https://www.sports-reference.com/stathead/basketball/player-span-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead)

  **Team Finders**:
  [Season Finder](https://www.sports-reference.com/stathead/basketball/team-season-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Game Finder](https://www.sports-reference.com/stathead/basketball/team-game-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Streak Finder](https://www.sports-reference.com/stathead/basketball/team-streak-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Span Finder](https://www.sports-reference.com/stathead/basketball/team-span-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead)

  **Other Finders**:
  [Versus Finder](https://www.sports-reference.com/stathead/basketball/versus-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Shot Finder](https://www.sports-reference.com/stathead/basketball/shot_finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead)

  **College Tools**:
  [Player Season Finder](https://www.sports-reference.com/stathead/basketball/cbb/player-season-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Player Game Finder](https://www.sports-reference.com/stathead/basketball/cbb/player-game-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Team Season Finder](https://www.sports-reference.com/stathead/basketball/cbb/team-season-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead),
  [Team Game Finder](https://www.sports-reference.com/stathead/basketball/cbb/team-game-finder.cgi?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footernav_stathead)
* [Coaches](/coaches/NBA_stats.html)

  [Richie Guerin](/coaches/gueriri01c.html),
  [Rudy Tomjanovich](/coaches/tomjaru01c.html),
  [Jim O'Brien](/coaches/obrieji99c.html),
  [Mike Fratello](/coaches/fratemi99c.html),
  [Alvin Gentry](/coaches/gentral99c.html)
  ...
* [Awards](/awards/)

  [NBA MVP](/awards/mvp.html),
  [All-NBA](/awards/all_league.html),
  [Defensive Player of the Year](/awards/dpoy.html),
  [Rookie of the Year](/awards/roy.html),
  [All-Rookie](/awards/all_rookie.html),
  [Hall of Fame](/awards/hof.html)
  ...
* [NBA Contracts](/contracts/)

  [Main Index](/contracts/),
  [Team Payrolls](/contracts/ATL.html),
  [Player Contracts](/contracts/players.html),
  [Glossary](/contracts/glossary.html)
  ...
* [Playoffs](/playoffs/)

  [2026 NBA Playoffs](/playoffs/NBA_2026.html),
  [2025 NBA Playoffs](/playoffs/NBA_2025.html),
  [2024 NBA Playoffs](/playoffs/NBA_2024.html),
  [2023 NBA Playoffs](/playoffs/NBA_2023.html),
  [2022 NBA Playoffs](/playoffs/NBA_2022.html),
  [2021 NBA Playoffs](/playoffs/NBA_2021.html),
  [2020 NBA Playoffs](/playoffs/NBA_2020.html),
  [Playoffs Series History](/playoffs/)
  ...
* [All-Star Games](/allstar/)

  [2026 All-Star Game](/allstar/NBA_2026.html),
  [2025 All-Star Game](/allstar/NBA_2025.html),
  [2024 All-Star Game](/allstar/NBA_2024.html),
  [2023 All-Star Game](/allstar/NBA_2023.html),
  [2022 All-Star Game](/allstar/NBA_2022.html),
  [2021 All-Star Game](/allstar/NBA_2021.html),
  [2020 All-Star Game](/allstar/NBA_2020.html)
  ...
* [NBA Draft](/draft/)

  [2025 Draft](/draft/NBA_2025.html),
  [2024 Draft](/draft/NBA_2024.html),
  [2023 Draft](/draft/NBA_2023.html),
  [2022 Draft](/draft/NBA_2022.html),
  [2021 Draft](/draft/NBA_2021.html),
  [2020 Draft](/draft/NBA_2020.html),
  [2019 Draft](/draft/NBA_2019.html)
  ...
* [Frivolities](/friv/)

  [Players who played for multiple teams](/friv/players-who-played-for-multiple-teams-franchises.fcgi)
  [(WNBA)](/wnba/friv/players-who-played-for-multiple-teams-franchises.fcgi),
  [Birthdays](/friv/birthdays.fcgi),
  [Colleges](/friv/colleges.fcgi),
  [High Schools](/friv/high_schools.fcgi),
  [Milestone Watch](/friv/milestones.fcgi)
  ...
* [Executives](/executives/NBA_stats.html)

  [Daryl Morey](/executives/moreyda99x.html),
  [Masai Ujiri](/executives/ujirima99x.html),
  [Pat Riley](/executives/rileypa01x.html),
  [Danny Ainge](/executives/aingeda01x.html),
  [Jon Horst](/executives/horstjo01x.html)
  ...
* [Referees](/referees/)

  [Joe Forte](/referees/fortejo99r.html),
  [Tony Brothers](/referees/brothto99r.html),
  [Dan Crawford](/referees/crawfda99r.html),
  [Ron Olesiak](/referees/olesiro99r.html),
  [David Jones](/referees/jonesda99r.html)
  ...
* [G League Stats](/gleague/)

  [Players](/gleague/players/),
  [Teams](/gleague/teams/),
  [Seasons](/gleague/years/),
  [Leaders](/gleague/leaders/),
  [Awards](/gleague/awards/)
  ...
* [International Basketball Stats](/international/)

  [Players](/international/players/),
  [Teams](/international/teams/),
  [Seasons](/international/years/),
  [Leaders](/international/leaders/),
  [Awards](/international/awards/)
  ...
* [WNBA](/wnba/)

  [Players](/wnba/players/),
  [Teams](/wnba/teams/),
  [Seasons](/wnba/years/),
  [Leaders](/wnba/leaders/),
  [Awards](/wnba/awards/),
  [All-Star Games](/wnba/allstar/),
  [Executives](/wnba/executives/)
  ...
* [NBL](/nbl/)

  [Players](/nbl/players/),
  [Teams](/nbl/teams/),
  [Seasons](/nbl/years/),
  [Leaders](/nbl/leaders/),
  [Awards](/nbl/awards/)
  ...
* [About](/about/)

  [Glossary](/about/glossary.html),
  [Contact and Media Information](/about/contact.html),
  [Frequently Asked Questions about the NBA, WNBA and Basketball](/about/nba-basketball-faqs.html),
  [NBA Data Coverage](/data/stats-coverage-game.html),
  [ABA Data Coverage](/data/stats-coverage-game-aba.html),
  ...
* [Immaculate Grid (Men's)](https://www.sports-reference.com/immaculate-grid/basketball/mens/?utm_campaign=2023_07_lnk_home_footer_ig&utm_source=bbr&utm_medium=sr_xsite) and [Immaculate Grid (Women's)](https://www.sports-reference.com/immaculate-grid/basketball/womens/?utm_campaign=2023_07_lnk_home_footer_ig&utm_source=bbr&utm_medium=sr_xsite)

  Put your basketball knowledge to the test with our daily basketball trivia games. Can you complete the grids?

* [Basketball-Reference.com Blog and Articles](https://www.basketball-reference.com/bbr-blog/)

## We're Social...for Statheads













**Site Last Updated:** Friday, July 10, 5:25AM

[Question, Comment, Feedback, or Correction?](https://www.sports-reference.com/feedback/)

[Subscribe to our Free Email Newsletter](https://www.basketball-reference.com/email)

[Subscribe to Stathead Basketball: Get your first month FREE  
*Your All-Access Ticket to the Basketball Reference Database*](https://www.sports-reference.com/stathead/sport/basketball/?utm_medium=sr_xsite&utm_source=bbr&utm_campaign=2023_01_footerbttn_stathead)

[Do you have a sports website? Or write about sports? We have tools and resources that can help you use sports data. Find out more.](https://www.sports-reference.com/blog/ways-sports-reference-can-help-your-website/?utm_medium=sr&utm_source=bbr&utm_campaign=site-footer-ways-help)

## FAQs, Tip & Tricks

* [Tips and Tricks from our Blog.](//www.sports-reference.com/blog/category/tips-and-tricks/)
* [Do you have a blog? Join our linker program.](/linker/)
* [Watch our How-To Videos to Become a Stathead](https://www.sports-reference.com/blog/category/stathead-tutorial-series/)
* [Subscribe to Stathead and get access to more data than you can imagine](https://www.sports-reference.com/stathead/?ref=bbr)

All logos are the trademark & property of their owners and not Sports Reference LLC. We present them here for purely educational purposes.
[Our reasoning for presenting offensive logos.](https://www.sports-reference.com/blog/2016/06/redesign-team-and-league-logos-courtesy-sportslogos-net/)

Logos were compiled by the amazing [SportsLogos.net.](http://sportslogos.net/)

Data Provided By
[![SportRadar](https://cdn.ssref.net/req/202606251/images/klecko/sportradar.png)](https://www.sportradar.com/)
the official stats partner of the NBA, NHL and MLB.

Copyright © 2000-2026 [Sports Reference LLC](//www.sports-reference.com/). All rights reserved.

The SPORTS REFERENCE, STATHEAD, IMMACULATE GRID, and IMMACULATE FOOTY trademarks are owned exclusively by Sports Reference LLC. Use without license or authorization is expressly prohibited.

* [Sports Reference ®](https://www.sports-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer)
* [Baseball](https://www.baseball-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer)
* [Football](https://www.pro-football-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer) [(college)](https://www.sports-reference.com/cfb/)
* [Basketball](https://www.basketball-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer) [(college)](https://www.sports-reference.com/cbb/)
* [Hockey](https://www.hockey-reference.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer)
* [Soccer](https://fbref.com/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer)
* [Blog](https://www.sports-reference.com/blog/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer)
* [Stathead ®](https://www.sports-reference.com/stathead/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer)
* [Immaculate Grid ®](https://www.sports-reference.com/immaculate-grid/basketball/mens/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_footer)

[About](//www.sports-reference.com/about.html) •
[Conditions & Terms of Service](//www.sports-reference.com/termsofuse.html) •
[Advertise With Us](//www.sports-reference.com/advertise.html)
•
[Jobs at SR](//www.sports-reference.com/jobs.html)
•
[Basketball-Reference.com T-Shirts & Store](https://sportsreference.threadless.com/)
•
[Your Privacy Choices](#)
  
  
Sports Reference Purpose: We will be the trusted source of information and tools that inspire and empower users to enjoy, understand, and share the sports they love.
  
  
[Privacy Policy](//www.sports-reference.com/privacy.html) •
[Gambling Revenue Policy](//www.sports-reference.com/gambling-revenue-policy.html) •
[Accessibility Policy](//www.sports-reference.com/accessibility-policy.html) •
[Use of Data](//www.sports-reference.com/data_use.html)






   