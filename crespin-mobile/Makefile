SRCDIR=src
LIBDIR=lib
BINDIR=bin
INCDIR=include
CC = gcc
#AR = ar
CFLAGS=-Wall -I$(INCDIR)
LDFLAGS=-L$(LIBDIR)
EXEC=crespin

all : $(BINDIR)/$(EXEC)

$(BINDIR)/crespin : $(SRCDIR)/communication.o $(SRCDIR)/crespin.o
	$(CC) $(LDFLAGS) -o $@ $(SRCDIR)/communication.o $(SRCDIR)/crespin.o -lpthread -lwiringPi -lm

$(SRCDIR)/%.o : $(SRCDIR)/%.c
	$(CC) -o $@ -c $< $(CFLAGS)

clean :
	rm $(BINDIR)/*
	rm $(SRCDIR)/*.o
	rm $(LIBDIR)/*.a
