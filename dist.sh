#!/bin/bash

if [ -e "SPtP.tar.gz" ]
then
    echo Removing old SPtP.tar.gz
    rm SPtP.tar.gz
fi

if [ -e "learning.tar" ]
then
    echo Removing old learning.tar
    rm learning.tar
fi

echo Copying files to temp folder

TEMP=`mktemp -d`
CURRENT=`pwd`

mkdir $TEMP/SPtP
cp $CURRENT/*.py $TEMP/SPtP
cp $CURRENT/README $TEMP/SPtP
cp $CURRENT/COPYING $TEMP/SPtP

mkdir $TEMP/SPtP/data
cp $CURRENT/data/factors.txt $TEMP/SPtP/data/factors.txt

mkdir $TEMP/SPtP/server
cp $CURRENT/server/index.html $TEMP/SPtP/server
cp -R $CURRENT/server/core $TEMP/SPtP/server
cp -R $CURRENT/server/lib $TEMP/SPtP/server

mkdir $TEMP/SPtP/tests
cp $CURRENT/tests/*.* $TEMP/SPtP/tests
cp -R $CURRENT/tests/negative $TEMP/SPtP/tests
cp -R $CURRENT/tests/batch_test_files $TEMP/SPtP/tests

mkdir $TEMP/learning
cp -R $CURRENT/learning/db $TEMP/learning
cp -R $CURRENT/learning/test $TEMP/learning

cp -R $CURRENT/__static__/input $TEMP/SPtP

cd $TEMP

echo Creating SPtP.tar.gz
tar czf SPtP.tar.gz SPtP
mv $TEMP/SPtP.tar.gz $CURRENT/

echo Creating learning.tar
tar cf learning.tar learning
mv $TEMP/learning.tar $CURRENT/

cd $CURRENT

rm -rf $TEMP
