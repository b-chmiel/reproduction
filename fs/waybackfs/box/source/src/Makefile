CFLAGS = -Wall -g -O2 -std=gnu90 `pkg-config fuse --cflags --libs`
OPTS = -D_FILE_OFFSET_BITS=64 -DDEBUG

wayback: wayback.c waybackfsvops.c waybackfs.h
	gcc $(CFLAGS) $(OPTS) wayback.c waybackfsvops.c -o wayback

clean:
	rm wayback
