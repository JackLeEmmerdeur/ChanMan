#ifndef FILEINOUT_H
#define FILEINOUT_H

#include <iostream>
#include <fstream>
#include <string>
#include <stdexcept>
#include <stdio.h>
#include <iomanip>

using namespace std;

class FileInOut
{
    public:
        ifstream in;
        ofstream out;
        string filepathin;
        string filepathout;

        FileInOut(string filepathin, string filepathout);
        ~FileInOut();

        void open();
        void assertNotOpened();
        void assertOpened();

    protected:

    private:
        bool isIfstreamOpen();
        bool isOfstreamOpen();
};

#endif // FILEINOUT_H
