select "ANALOG", sname, major_channel from ANALOG WHERE sname IS NOT NULL
UNION
select "FREE_RADIO_DVB_C", sname, major_channel from FREE_RADIO_DVB_C WHERE sname IS NOT NULL 
UNION
select "FREE_TV_DVB_C", sname, major_channel from FREE_TV_DVB_C WHERE sname IS NOT NULL 
UNION
select "RADIO_DVB_C", sname, major_channel from RADIO_DVB_C WHERE sname IS NOT NULL 
UNION
select "TV_DVB_C", sname, major_channel from TV_DVB_C WHERE sname IS NOT NULL 
UNION
select "HDTV_DVB_C", sname, major_channel from HDTV_DVB_C WHERE sname IS NOT NULL 
ORDER BY major_channel;