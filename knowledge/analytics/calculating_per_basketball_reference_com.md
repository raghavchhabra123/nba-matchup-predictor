Calculating PER | Basketball-Reference.com



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

[BBR Home Page](/)  > [About](/about/)  > **Calculating PER**

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

# Calculating PER

The Player Efficiency Rating (PER) is a per-minute rating developed by
ESPN.com columnist [John Hollinger](http://sports.espn.go.com/keyword/search?searchString=John_Hollinger
). In John's words, "The PER sums up all a player's
positive accomplishments, subtracts the negative accomplishments, and
returns a per-minute rating of a player's performance." It appears from
his books that John's database only goes back to the 1988-89 season. I
decided to expand on John's work and calculate PER for all players since
minutes played were first recorded (1951-52).

All calculations begin with what I am calling unadjusted PER (uPER). The
formula is:

```
uPER = (1 / MP) *
     [ 3P
     + (2/3) * AST
     + (2 - factor * (team_AST / team_FG)) * FG
     + (FT *0.5 * (1 + (1 - (team_AST / team_FG)) + (2/3) * (team_AST / team_FG)))
     - VOP * TOV
     - VOP * DRB% * (FGA - FG)
     - VOP * 0.44 * (0.44 + (0.56 * DRB%)) * (FTA - FT)
     + VOP * (1 - DRB%) * (TRB - ORB)
     + VOP * DRB% * ORB
     + VOP * STL
     + VOP * DRB% * BLK
     - PF * ((lg_FT / lg_PF) - 0.44 * (lg_FTA / lg_PF) * VOP) ]
```

Most of the terms in the formula above should be clear, but let me define
the less obvious ones:

```
factor = (2 / 3) - (0.5 * (lg_AST / lg_FG)) / (2 * (lg_FG / lg_FT))
VOP    = lg_PTS / (lg_FGA - lg_ORB + lg_TOV + 0.44 * lg_FTA)
DRB%   = (lg_TRB - lg_ORB) / lg_TRB
```

I am not going to go into details about what each component of the PER is
measuring; that's why John writes and sells books.

Problems arise for seasons prior to 1979-80:

* 1979-80 — debut of 3-point shot in NBA
* 1977-78 — player turnovers first recorded in NBA
* 1973-74 — player offensive rebounds, steals, and blocked shots first
  recorded in NBA

The calcuation of uPER obviously depends on these statistics, so here are
my solutions for years when the data are missing:

* Zero out three-point field goals, turnovers, blocked shots, and
  steals.
* Set the league value of possession (VOP) equal to 1.
* Set the defensive rebound percentage (DRB%) equal to 0.7.
* Set player offensive rebounds (ORB) equal to 0.3 \* TRB.

Some of these solutions may not be elegant, but I think they are
reasonable. After uPER is calculated, an adjustment must be made for the
team's [pace](/about/glossary.html#pace). The pace adjustment
is:

```
pace adjustment = lg_Pace / team_Pace
```

League and team pace factors cannot be computed for seasons prior to
1973-74, so I estimate the above using:

```
estimated pace adjustment = 2 * lg_PPG / (team_PPG + opp_PPG)
```

To give you an idea of the accuracy of these estimates, here are the actual
pace adjustments and the estimated pace adjustments for teams from the
Eastern Conference in 2002-03:

```
Tm       Act       Est

ATL     1.00      0.99
BOS     1.00      1.02
CHI     0.97      0.98
CLE     0.97      0.99
DET     1.05      1.06
IND     0.99      1.00
MIA     1.04      1.08
MIL     1.01      0.96
NJN     0.99      1.03
NOH     1.01      1.02
NYK     1.00      0.98
ORL     0.98      0.97
PHI     1.00      0.99
TOR     1.01      1.01
WAS     1.03      1.03
```

For all seasons where actual pace adjustments can be computed, the root
mean square error of the estimates is 0.01967.

Now the pace adjustment is made to uPER (I will call this aPER):

```
aPER = (pace adjustment) * uPER
```

The final step is to standardize aPER. First, calculate league average
aPER (lg\_aPER) using player minutes played as the weights. Then, do the
following:

```
PER = aPER * (15 / lg_aPER)
```

The step above sets the league average to 15 for all seasons.

Those are the gory details. If you have any comments or questions, please
send me some [feedback](/feedback).

* Welcome  · [Your Account](https://www.sports-reference.com/profile/?utm_source=bbr&utm_medium=sr_xsite&utm_campaign=2023_01_srnav_account)
* [Logout](https://www.sports-reference.com/users/logout.cgi)
* [Ad-Free Login](https://www.sports-reference.com/users/login.cgi?token=1)
* [Create Account](https://www.sports-reference.com/stathead/signup.cgi)

You are here: [BBR Home Page](/)  > [About](/about/)  > **Calculating PER**

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






   