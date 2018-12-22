homedir:getenv`HOME
datadir:hsym`$homedir,"/chess/uscf/kdb"
supdir:hsym`$homedir,"/chess/uscf/unzipped"
topdir:hsym`$homedir,"/chess/uscf/top100"

normrating:"I"$except[;"*"]each
extractmonth :{[f]"M"$"20",first "/"vs (1+count string supdir) _ string[f]}
extractmonth2:{[months;f]a:" "vs f; "M"$a[1],".", months`$3#a 0}Months:`Jan`Feb`Mar`Apr`May`Jun`Jul`Aug`Sep`Oct`Nov`Dec!-2#'"0",'string 1+til 12
MonthMap:{til[count x]!x}key Months
getsupfiles:{[supdir] files:{x where x like "*.txt"}lower hsym each `$system"find ", 1_string supdir}

//parse suppliment files
parsesup:{[f]
 t:flip`name`id`expdate`state`regrating`quickrating!("*JDS**";"\t")0:read0 0N!f;
 t:update regrating:normrating regrating, quickrating:normrating quickrating from t;
 t:update month:extractmonth f from t;
 `month xcols t}

//ignore these *_More Quick Lists:Women | Correspondence
extractcategory:{
 x:except[;("under";"and";"over")]" "vs trim lower x;
 $[x[0]in("age";"under"); (`overall;`regular;"I"$last x); 
   x[0]~"girls"; (`female;`regular;"I"$last x); 
   x[0]in("quick";"blitz"); ($[x[1]in("girls";"women");`female;`overall];`$x 0;"I"$last x); 
   x[0]in("top";"overall");   (`overall; $[x[2]~"quick";`quick;`regular]; 0Ni);
   x[0]~"women"; (`female;`regular; "I"$last x)]
 }

 //extract gender[`overall`girl`woman] timecontrol[`regular`quick`blitz] agegroup[7 8 9...16 21 50 0N means all]
parsetop100:{[f] 
 a:"_"vs string[f]; m:extractmonth2 a 0; if[m<2008.02m; :()]; //don't slurp in older files with wierd format
 d:`gender`timecontrol`age!extractcategory a 1;
 t:flip`rnk`name`age`state`country`rating!("**ISSI";"\t")0:` sv topdir,0N!f;
 t:update rnk:fills "I"$rnk from delete country from select from t where not null state;
 t:update id:{"I"$-1_'(1+first each ss[;"("]'[x]) _'x}t`name from t;
 t:update month:m, rnkgender:d`gender, rnktimecontrol:d`timecontrol, age:d`age from t;
 `month`rnkgender`rnktimecontrol`age`rnk`id`name xcols t}

parsetokdb:{
 (` sv datadir,`sup) set `month xasc raze t:parsesup each getsupfiles supdir;
 //if the file has a trailing space, it's the file contraining foreign players, we will ingore those files
 (` sv datadir,`top100) set `month`rnkgender`rnktimecontrol`age`rnk xasc raze a:parsetop100 each files:distinct{x where not any lower[x] like/:("*more*";"*correspondence*"; "* ")}key topdir;
 }

loadtokdb:{
 `sup set select from get[` sv datadir,`sup] where month>=2008.02m;
 `top100 set get` sv datadir,`top100;
 }

appendsup:{[m]
 if[0<n:count select from sup where month=m; 'string[n]," rows exists for month ", string m];
 m:`$except[2 _ string m;"."]; 
 .[` sv datadir,`sup;();,; ] parsesup` sv supdir, m,`$"RSQ",string[m], "T.TXT";
 }

loadtokdb[]

delta:{0^(0^x[-1]),1 _ x:deltas x}

tabledir:`:/Users/yetian/Downloads/table
N:20

analytics:{
 //biggest one month rating jump
 drating:update dreg:delta regrating, prevregrating:prev regrating, dmon:delta month by id from sup;
 (` sv tabledir,`ratingjump.csv)0:","0:`month`name`id`state`regrating`prevregrating xcols delete quickrating,dmon from N#`dreg xdesc select from drating where dmon=1
 (` sv tabledir,`ratingjump.csv)0:","0:`month`name`id`state`regrating`prevregrating xcols delete quickrating,dmon from N#`dreg xdesc select from drating where dmon=1, prevregrating>=2200
 }

\

group first each " "vs'(distinct trim each last each"_"vs'string files)
(distinct trim each last each"_"vs'string files) 31 32 33 34 35 36 37 38 41 42 43 44 45 46
{x where x like "*more*"}lower(distinct trim each last each"_"vs'string files)


count a:`regrating xdesc delete month,quickrating from select from sup where month=2018.12m, regrating within 1900 2300, state in `PA`CT`NY`NJ, id in exec id from top100 where month=2018.11m, rnkgender=`overall, rnktimecontrol=`regular, not null age, age<=14

//stddev
`:/Users/yetian/Downloads/table/mm2.csv 0:"," 0:select month:MonthMap x, avg_rating_change:avgchg from select avgchg:avg dreg, stddevchg:dev dreg  by month mod 12 from drating where dmon=1, regrating>=1700

