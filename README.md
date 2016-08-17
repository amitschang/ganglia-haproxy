# ganglia-haproxy
ganglia plugin for collecting haproxy stats

Update of original version hosted at:

https://bitbucket.org/fahdsultan/ganglia-haproxy

where updates include reading and transmitting all frontends and
backends without the need to explicitly configure them, in addition to
buffering the read of stats socket (instead of for each metric update).