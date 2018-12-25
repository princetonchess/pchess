
zipdir=~/chess/twic/zipped
if [ ! -d $zipdir ]
then
  mkdir -p  $zipdir
  mkdir -p  $zipdir/../pgn
fi

wget http://www.theweekinchess.com/zips/twic${1}g.zip
unzip twic${1}g.zip -d ../pgn/
