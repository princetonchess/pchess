
zipdir=~/chess/twic/zipped
if [ ! -d $zipdir ]
then
  mkdir -p  $zipdir
  mkdir -p  $zipdir/../pgn
fi

cd $zipdir
for i in {1233..1258}
do
	wget http://www.theweekinchess.com/zips/twic${i}g.zip
	unzip twic${i}g.zip -d ../pgn/
done
