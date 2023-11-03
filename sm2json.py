import os
import sys
import shutil
import simfile
from simfile.ssc import SSCSimfile
from simfile.types import Chart, Charts, Simfile
from simfile.notes import NoteData
from simfile.notes.count import *
from simfile.timing.displaybpm import displaybpm
import json

# Things that I probably want to do
# For relative path gfx - if the banner is a duplicate, don't copy the banner to save space (TPE style, fallback banners, etc)
# Make "hasMods" field parse correctly

cwd = os.getcwd()

chartlist = {
	"packName": "", 
	"packBanner": "",
	"charts": []}
songIndex = 0

def getChartData(simfileDir: any):
	path = simfileDir.simfile_path

	with simfile.mutate(path) as sim:
		# Get DisplayBPM
		disp = displaybpm(sim)
		formattedDisplayBPM = [(str)(disp.min), (str)(disp.max)]

		# Convert banner/jacket names and copy them to the output folder
		# ash you are saving my goddamn life right now, i was about to do some dumbass pathlib crap to find graphics
		bnpath = simfileDir.assets().banner
		jkpath = simfileDir.assets().jacket
		bnpathFinal = ""
		jkpathFinal = ""
		# In case some fucker has .jpg banners, i do not want to assume everyone uses .png and hardcode this lol
		if bnpath != None:
			bnext = bnpath.split(".")[-1]
			shutil.copyfile(bnpath, f"./output/bn-{songIndex}.{bnext}")
			bnpathFinal = f"./bn-{songIndex}.{bnext}"
		if jkpath != None:
			jkext = jkpath.split(".")[-1]
			shutil.copyfile(jkpath, f"./output/jk-{songIndex}.{jkext}")
			jkpathFinal = f"./jk-{songIndex}.{bnext}"

		# Create a dict for the metadata to insert into the array that will be converted to JSON later
		# Definitely the most efficient way to do this, i am highly intelligent :clueless:
		meta = {
			"sid": songIndex, # Song ID

			"title": sim.title, # Song title
			"titletranslit": sim.titletranslit, # Transliterated title
			"subtitle": sim.subtitle, # Subtitle
			"subtitletranslit": sim.subtitletranslit, # Transliterated subtitle
			"artist": sim.artist, # Song artist
			"artisttranslit": sim.artisttranslit, # Transliterated artist
			
			"displaybpm": formattedDisplayBPM, # Song's display BPM

			"bnpath": bnpathFinal, # Path to banner in output folder
			"jkpath": jkpathFinal, # Path to jacket in output folder
			# We skip backgrounds because that's more filesize and also I can't think of a use case where you would want bg over bn x_x
			# (maybe a bad idea)

			"difficulties": []
		}
	
		# Checking for mods and gimmicks
		hasmods = True if (sim.fgchanges != None) | (sim.attacks != None) else False

		# Parse individual difficulties
		for chart_ in sim.charts:
			chart: Chart = chart_ # typing workaround

			# Count number of notes
			notedata = NoteData(chart)
			notecount = count_steps(notedata)
			
			# Checking for ssc specific fields
			credit = chart.credit if chart.credit != None else ""
			chartname = chart.chartname if chart.chartname != None else ""

			# Checking for difficulty-specific mods
			if chart.attacks != None: hasmods = True

			# Difficulty specific metadata
			diff = {

				"slot": chart.difficulty, # Difficulty slot of the chart - Challenge, Hard, Medium, etc 
				"type": chart.stepstype, # Steps type - Singles, Doubles, etc
				"difficulty": chart.meter, # The difficulty number assigned to the chart. Always 100% accurate and never subject to community debate 
				
				"notecount": notecount, # Number of notes, as specified by StepMania ingame

				"description": chart.description, # Chart's description field
				"credit": credit, # Chart specific credit - ssc only
				"chartname": chartname, # Chart's chartname - ssc only

				###
				#	Ideally, I'd like to get the "hasmods" field working, but right now it's just not parsing correctly lol
				#	I've been testing on the TPE1 pack and I think #ATTACKS having one newline has something to do with it
				#	probably just strip() the text? idfk
				#	nvm, now it's giving me "NoneType has no attribute strip()" but if i check for not being none then it still says there's mods. ok
				###
				#"hasmods": hasmods # True if the simfile has FGCHANGES or ATTACKS
				# I considered a "hasgimmicks" field, but I feel like that's considerably less useful due to stuff like BermudaTriangle or CMOD ok charts
			}

			meta["difficulties"].append(diff)
		
		# Add final song metadata w/ all difficulties to overall chart list 
		chartlist["charts"].append(meta)

def main():
	global songIndex
	global chartlist

	args = sys.argv[1:]
	packPath = args[0]
	# Make an output folder in the current working directory
	if not os.path.exists(f"{cwd}/output"):
		os.makedirs(f"{cwd}/output")

	try:
		simPack = simfile.dir.SimfilePack(packPath)
		
		# Get pack banner and copy it to output folder
		packbnPath = simPack.banner()
		packbnPathFinal = ""
		if packbnPath != None:
			bnext = packbnPath.split(".")[-1]
			shutil.copyfile(packbnPath, f"./output/bn-pack.{bnext}")
			packbnPathFinal = f"./bn-pack.{bnext}"
		# Append pack metadata to JSON
		chartlist["packName"] = simPack.name
		chartlist["packBanner"] = packbnPathFinal
		
		# Parse simfiles for metadata - prioritize ssc
		for simfileDir in simPack.simfile_dirs():
			getChartData(simfileDir)
			songIndex += 1

		# Convert the resulting chart list to a JSON string
		chartJSON = json.dumps(chartlist)

		# Write JSON to file
		f = open(f"{cwd}/output/pack.json", "w")
		f.write(chartJSON)
		f.close()

	except:
		if len(packPath) == 0:
			raise Exception("Must specify a path to a simfile pack")
		else:
			raise Exception("Something else went wrong lol")

if __name__ == "__main__":
	main() 