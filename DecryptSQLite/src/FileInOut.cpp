#include "FileInOut.h"

FileInOut::FileInOut(string filepathin, string filepathout)
{
    this->filepathin = filepathin;
    this->filepathout = filepathout;
}

FileInOut::~FileInOut()
{
    if (this->isIfstreamOpen())
        this->in.close();
    if (this->isOfstreamOpen())
        this->out.close();
}


void FileInOut::open()
{
    assertNotOpened();
    this->in.open(this->filepathin.c_str(), ios_base::in | ios_base::binary);
    this->out.open(this->filepathout.c_str(), ios_base::out | ios_base::binary);
    assertOpened();
}

bool FileInOut::isIfstreamOpen()
{
    return this->in && this->in.is_open();
}

bool FileInOut::isOfstreamOpen()
{
    return this->out && this->out.is_open();
}

void FileInOut::assertNotOpened()
{
    if (this->isIfstreamOpen())
        throw("ifstream already opened");

    if (this->isOfstreamOpen())
        throw("ofstream already opened");
}

void FileInOut::assertOpened()
{
    if (!this->isIfstreamOpen())
        throw("ifstream not opened");

    if (!this->isOfstreamOpen())
        throw("ofstream not opened");
}
