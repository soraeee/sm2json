# sm2json
Utility for converting simfile pack metadata into JSON  

## Dependencies  
```bash
pip install simfile
pip install wand
```

## Usage  
`py sm2json.py <path/to/pack> [-m|--minify]`  
This will create an `output` folder in your current working directory with banner/jacket art from the pack and a `pack.json` file.

The `-m`/`--minify` option minifies images, primarily to be used in web-based projects.

## Notes  
- Ideally I'd like a field that signifies whether a chart has mods or not via parsing `#ATTACKS`/`#FGCHANGES` but I got stuck on that