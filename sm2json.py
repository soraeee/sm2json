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
import hashlib
from wand.image import Image

# Things that I probably want to do
# Make "hasMods" field parse correctly

cwd = os.getcwd()

chartlist = {
	"packName": "", 
	"packBanner": "",
	"charts": []
}
imageHashes = []
songIndex = 0

def getHash(filename):
	return hashlib.md5(open(filename,'rb').read()).hexdigest()[:10]

def getChartData(simfileDir: any, minify):
	path = simfileDir.simfile_path

	with simfile.mutate(path) as sim:
		# Get DisplayBPM
		disp = displaybpm(sim)
		formattedDisplayBPM = [float(disp.min), float(disp.max)]
		
		# Create a bg/jacket/banner to use as a graphic
		# A background is prefered, but fallback to jacket or bn if not found
		# A hash will be used to check for duplicate graphics (probably not very efficient?)
		bnpath = simfileDir.assets().banner
		jkpath = simfileDir.assets().jacket
		bgpath = simfileDir.assets().background
		gfxPath = ""
		gfxHash = ""
		if bnpath != None:
			gfxPath = bnpath
			gfxHash = getHash(bnpath)
		elif jkpath != None:
			gfxPath = jkpath
			gfxHash = getHash(jkpath)
		elif (bgpath != None) and (minify):
			gfxPath = bgpath
			gfxHash = getHash(bgpath)
		# We use Wand (ImageMagick) to make a jpeg
		gfxRendered = f"{gfxHash}.jpg"
		if gfxHash not in imageHashes:
			imageHashes.append(gfxHash)
			with Image(filename=gfxPath) as img:
				img = Image(image=img.sequence[0]) if len(img.sequence) > 1 else img
				if minify == True:
					w = img.width
					h = img.height
					if (w < 900) or (h < 100):
						factor = max(900/w, 100/h)
						img.resize(int(factor*w), int(factor*h))
						w = img.width
						h = img.height
					img.blur(radius=0, sigma=4.5)
					img.crop(int((w-900)/2), int((h-100)/2), width=900, height=100)
				img.format = 'jpeg'
				img.save(filename=f"./output/{gfxHash}.jpg")

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
			"gfxPath": gfxRendered, # Path to gfx
			"difficulties": []
		}
	
		# Checking for mods and gimmicks
		#hasmods = True if (sim.fgchanges != None) | (sim.attacks != None) else False

		# Parse individual difficulties
		for chart_ in sim.charts:
			chart: Chart = chart_ # typing workaround

			# Count number of notes
			notedata = NoteData(chart)
			notecount = count_steps(notedata)
			
			# Checking for ssc specific fields
			credit = ""
			chartname = ""
			if sim == SSCSimfile:
				credit = chart.credit
				chartname = chart.chartname

			# Checking for difficulty-specific mods
			#if chart.attacks != None: hasmods = True

			# Difficulty specific metadata
			diff = {

				"slot": chart.difficulty, # Difficulty slot of the chart - Challenge, Hard, Medium, etc 
				"type": chart.stepstype, # Steps type - Singles, Doubles, etc
				"difficulty": int(chart.meter), # The difficulty number assigned to the chart. Always 100% accurate and never subject to community debate 
				
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
	minify = False
	if len(args) > 1:
		minify = (args[1] == '-m') or (args[1] == '--minify')

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
			getChartData(simfileDir, minify)
			songIndex += 1

		# Convert the resulting chart list to a JSON string
		chartJSON = json.dumps(chartlist)

		# Write JSON to file
		f = open(f"{cwd}/output/pack.json", "w")
		f.write(chartJSON)
		f.close()

	# "Exception" "handler"
	except:
		if len(packPath) == 0:
			raise Exception("Must specify a path to a simfile pack")
		else:
			raise Exception("Something else went wrong lol")

if __name__ == "__main__":
	main() 