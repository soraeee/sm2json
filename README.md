# sm2json
Utility for converting simfile pack metadata into JSON  

## Dependencies  
`pip install simfile`  

## Usage  
`py sm2json.py <path to pack>`  
This will create an `output` folder in your current working directory with banner/jacket art from the pack and a `pack.json` file.

## Notes  
- Charts that refer to the same banner via relative paths (e.g. fallback banners) will be duplicated in the output folder. I still need to figure out how to make this not happen
- Ideally I'd like a field that signifies whether a chart has mods or not via parsing `#ATTACKS`/`#FGCHANGES` but I got stuck on that
- `displaybpm` field should probably be an array
