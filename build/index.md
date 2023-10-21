https://www.metachris.com/2016/03/how-to-install-qt56-pyqt5-virtualenv-python3/

### ⚠️ Warning

* This How-To is for Debian-based distributions
* The build-scripts for a Win32 executable are included but undocumented 
* It is a lot of hassle to get right and maybe won't work
* It is very outdated
* The application should be ported to Qt CPP instead

## 1. Download prerequisites

#### sip-4.18.1
https://sourceforge.net/projects/pyqt/files/sip/sip-4.18.1/sip-4.18.1.tar.gz


#### QT 5.4.2
https://download.qt.io/archive/qt/5.4/5.4.2/qt-opensource-linux-x64-5.4.2.run


#### PyQt-gpl-5.4.2
https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.2/PyQt-gpl-5.4.2.tar.gz

#### icu53
https://de.osdn.net/projects/sfnet_icu/downloads/ICU4C/53.1/icu4c-53_1-src.tgz/


## 2. Create directories
```bash
mkdir ~/Documents/Projekte/Python/compiled
mkdir ~/Documents/Projekte/Python/environments
mkdir ~/Documents/Projekte/Python/sources
```

## 3. Install QT

```bash
cd ~/Downloads
 chmod +x qt-opensource-linux-x64-5.4.2.run
./qt-opensource-linux-x64-5.4.2.run
```

* Deselect functions not needed

* Install in "/home/<user>" or "/opt/"


## 4. Install Python3.5
```bash
sudo apt-get install python3.5
```

## 5. Install Python3.5 sources
```bash
sudo apt-get install python3.5-dev
```

## 6. Install Pip3
```bash
sudo apt-get python3-pip
```

## 7. Install virtualenv
```bash
pip3 install virtualenv
```

## 8. Create Virtualenv
```bash
cd /home/user/Documents/Projekte/Python/environments
virtualenv projectenv --no-site-packages
```

## 9. Activate Python virtualenvironment
```bash
cd ~/Documents/Projekte/Python/environments/projectenv
source bin/activate
```

## 10. Build sip
```bash
cp ~/Downloads/sip-4.18.1.tar.gz ~/Dokumente/Projekte/Python/compiled
cd ~/Dokumente/Projekte/Python/compiled
tar -xzvf sip-4.18.1.tar.gz
cd sip-4.18.1
python3.5 configure.py -d /home/buccaneersdan/Dokumente/Projekte/Python/environments/ChanManEnv/lib/python3.5/site-packages/
make
make install
```

## 11. Strip down ICU53
```bash
mv ~/Downloads/icu4c-53_1-src.tgz ~/Documents/Projeke/Python/compiled
cd ~/Documents/Projeke/Python/compiled
tar -gzfv icu4c-53_1-src.tgz
cd ~/Documents/Projeke/Python/compiled/icu/source/data/in/
mv icudt53l.dat icudt53l.dat.save
```

Go to: http://apps.icu-project.org/datacustom/ICUData53.html

Create stripped dat with only your local language options

Save as icudt53l.dat under ~/Documents/Projeke/Python/compiled/icu/source/data/in/
```bash
cd ~/Documents/Projeke/Python/compiled/icu/source
./configure
make
cp ~/Documents/Projeke/Python/compiled/icu/source/lib/* ~/Qt5.4.2
(Pick what you chose in "3. Install QT" for "~/Qt5.4.2")
```

## 12. libstreamer-010.so.0
```bash
  sudo nano /etc/apt/sources.list.d/mx.list
```

Add:
```
deb http://httpredir.debian.org/debian jessie main
```

```bash
sudo nano /etc/apt/preferences.d/01_release
```
Add:
```
  Package: *
  Pin: release o=Debian,a=unstable
  Pin-Priority: 600

  Package: *
  Pin: release o=Debian,n=jessie
  Pin-Priority: 10
```

```bash
sudo apt-get install libgstreamer0.10-0 libgstreamer-plugins-base0.10-0
```

## 13. Build PyQt5

#### Extract PyQt-sources
  
```bash
mv ~/Downloads/PyQt-gpl-5.4.2.tar.gz ~/Documents/Projeke/Python/compiled
cd ~/Downloads/Projeke/Python/compiled/PyQt-gpl-5.4.2
```

#### Copy "PyQt.build.config" and "PyQt.build.sh" in current dir

##### Configure minimal PyQt-Build

```bash
  chmod +x PyQt.build.sh
  ./PyQt.build.sh
  # $ yes
```

##### Install PyQt in virtual environments
```bash
make
sudo make install
```

## 14. Install python libs

```bash
pip3 install --upgrade setuptools
# or
pip install ez_setup
pip install unroll
```

```bash
pip3 install wheel
pip3 install yattag sortedcontainers ruamel.yaml ijson pyinstaller plumbum chardet six
```

## 15. Install upx
```bash
sudo apt-get install upx-ucl
```

## 16. Compile icons and windows

Execute `compileIcons_linux.sh` and `compileWindows_linux.sh` from `resources/qtscripts`

## 17. Build the application
```bash
python setup.py build
```