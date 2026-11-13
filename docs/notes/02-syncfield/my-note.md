# 02 · SyncField · My note

What I understood from [concept.html](concept.html) and the labs, in my own words. Free form.

The order is sync_point -> armed -> 200ms wait (expect anchor) -> start chirp -> stop chirp.  
This is under the premise that worker starts data collecting task after start chirp sound.  

sync_point pairs monotonic clock and wall time. Only one exists in a session.  
Armed is the shared start line: data arriving after it gets recorded.  
Time between sync_point and armed is shared for all streams.  
There exists 200ms of wait time before start chirp sound.  
During this time, all streams are expected to have anchor time.  
Meaningful tactile data comes after start chirp.

Anchor time is when the first data arrived after the armed time. It exists per stream.  
Time between armed and anchor differs for each stream.
