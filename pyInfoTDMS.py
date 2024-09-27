from nptdms import TdmsFile

# Open the TDMS file
tdms_file = TdmsFile.open(r'Test Data/Test Data.tdms')

# List the groups inside the file
group_names = tdms_file.groups()
print("Groups in the TDMS file:")
for group in group_names:
    print(group.name)

# Access a specific channel
group_name = 'Data'  # Replace with your actual group name
channel_name = 'frame 0'  # Replace with your actual channel name

channel = tdms_file[group_name][channel_name]
print(f"Length of one frame '{channel_name}':", len(channel))
# Print the channel object
print(channel)