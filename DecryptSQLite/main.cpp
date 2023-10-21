#include <iostream>
#include <fstream>
#include <string>
#include <stdexcept>
#include <stdio.h>
#include <iomanip>
#include "FileInOut.h"

using namespace std;

int main(int argc, char *argv[])
{
    try
	{
        if (argc != 3)
            throw("ProggyMcProgsaen expects 2 argz");

        unsigned char c, co;
        char *chars = new char[1];
        int chiffre = 0x0388, step = 0, fpsize;

        FileInOut f(
            argv[1],
            argv[2]
        );

        f.open();

        f.in.seekg (0, ios_base::end);
        fpsize = f.in.tellg();
        f.in.seekg (0, ios_base::beg);

        for(int i=0; i<fpsize; i++)
        {
            f.in.read(chars, 1);

            c = chars[0];
            co = c ^ (chiffre >> 8);
            chars[0] = co;

            if (++step < 256)
            {
                chiffre += c + 0x96A3;
            }
            else
            {
                chiffre = 0x0388;
                step = 0;
            }

            f.out.write(chars, 1);

//            cout << a << ") " << (unsigned int)c << ":0x" << setfill('0') << setw(2) << hex << uppercase << +c << nouppercase << dec << endl;
//            cout << (unsigned int)co << ":0x" << setfill('0') << setw(2) << hex << uppercase << +co << nouppercase << dec << endl << "=========" << endl;
        }
	}
	catch(exception &ex)
	{
        cerr << ex.what() << endl;
		return 1;
    }
    catch (const std::string &ex)
	{
        cerr << ex << endl;
        return 2;
	}
    catch (char const *ex)
	{
        cerr << ex << endl;
        return 3;
	}
    return 0;
}

