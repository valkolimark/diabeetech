"""
STT Post-processor to correct common misheard phrases
Especially focused on timer commands that are commonly misheard

Migrated from itiflux voice_assistant/stt_post_processor.py
- Removed PyQt5 dependencies
- ALL 400+ correction rules preserved verbatim
"""

import re
from typing import Dict, List


class STTPostProcessor:
    """Post-process STT output to fix common misrecognitions"""

    def __init__(self):
        # Common misheard phrases and their corrections
        # Focus on timer-related corrections
        self.corrections = {
            # Timer misheard as "time of/or/are"
            r'\btime of\b': 'timer',
            r'\btime or\b': 'timer',
            r'\btime are\b': 'timer',
            r'\btime her\b': 'timer',
            r'\btime our\b': 'timer',
            r'\btimer of\b': 'timer',

            # Remove misheard as other words
            r'\bremove the time of\b': 'remove the timer',
            r'\bremove the time or\b': 'remove the timer',
            r'\bdelete the time of\b': 'delete the timer',
            r'\bdelete the time or\b': 'delete the timer',
            r'\bclear the time of\b': 'clear the timer',
            r'\bcancel the time of\b': 'cancel the timer',

            # Common insulin/correction misheards
            r'\binsulin time or\b': 'insulin timer',
            r'\binsulin time of\b': 'insulin timer',
            r'\bcorrection time or\b': 'correction timer',
            r'\bcorrection time of\b': 'correction timer',

            # Plural forms
            r'\btime ors\b': 'timers',
            r'\btime ofs\b': 'timers',
            r'\btime ares\b': 'timers',

            # Common STT mistakes with numbers
            r'\btoo units\b': 'two units',
            r'\bto units\b': 'two units',
            r'\bfor units\b': 'four units',

            # "for/four" corrections with food context
            r'\bfor slices?\b': 'four slices',
            r'\bfor pieces?\b': 'four pieces',
            r'\bfor cups?\b': 'four cups',
            r'\bfor grams?\b': 'four grams',
            r'\bfor carbs?\b': 'four carbs',

            # "too/to/two" corrections with food context
            r'\btoo slices?\b': 'two slices',
            r'\bto slices?\b': 'two slices',
            r'\btoo pieces?\b': 'two pieces',
            r'\bto pieces?\b': 'two pieces',
            r'\btoo cups?\b': 'two cups',
            r'\bto cups?\b': 'two cups',
            r'\btoo grams?\b': 'two grams',
            r'\bto grams?\b': 'two grams',

            # Common mishears for insulin phrases
            r"\bno of alzheimer's\b": 'two more units of insulin',
            r"\balzheimer's\b": 'timers',
            r'\bmore units\b': 'more units',

            # Meal type corrections
            r'\blunched\b': 'lunch',
            r'\bdinnered\b': 'dinner',
            r'\bbreakfasted\b': 'breakfast',

            # Additional number homophones
            r'\bwon unit\b': 'one unit',
            r'\bwon more unit\b': 'one more unit',
            r'\bsex units\b': 'six units',
            r'\bsex more units\b': 'six more units',
            r'\btree units\b': 'three units',  # "tree units" -> "three units"
            r'\btree more units\b': 'three more units',
            r'\btree slices\b': 'three slices',
            r'\btree carbs\b': 'three carbs',
            r'\btree grams\b': 'three grams',
            r'\bate units\b': 'eight units',  # "ate units of insulin" -> "eight units of insulin"
            r'\bate more units\b': 'eight more units',
            r'\bate grams\b': 'eight grams',
            r'\bate carbs\b': 'eight carbs',
            r'\bnein units\b': 'nine units',  # "nein units" -> "nine units"
            r'\bnein more units\b': 'nine more units',
            r'\bten units\b': 'ten units',  # Keep as is but ensure proper recognition
            r'\btin units\b': 'ten units',  # "tin units" -> "ten units"
            r'\btin more units\b': 'ten more units',

            # Food homophones
            r'\bstake\b': 'steak',  # "I ate stake" -> "I ate steak"
            r'\bmeet\b(?! with| you| me)': 'meat',  # "I had meet" -> "I had meat" (but not "meet with")
            r'\bserial\b(?! number| code)': 'cereal',  # "ate serial" -> "ate cereal"
            r'\bbury\b': 'berry',  # "I ate a bury" -> "I ate a berry"
            r'\bchilly\b(?! weather| outside)': 'chili',  # "bowl of chilly" -> "bowl of chili"
            r'\bflower\b(?= bread| tortilla| for)': 'flour',  # "flower tortilla" -> "flour tortilla"
            r'\bbred\b': 'bread',  # "I ate bred" -> "I ate bread"
            r'\bpair\b(?= of)': 'pear',  # "ate a pair" -> "ate a pear" (when followed by "of")
            r'\bpears of\b': 'pairs of',  # correction for above
            r'\bbeet\b': 'beet',  # Keep as is but ensure it doesn't become "beat"
            r'\bbeats\b(?! per| music)': 'beets',  # "I ate beats" -> "I ate beets"
            r'\bwrap\b(?= sandwich| for)': 'wrap',  # Keep as is
            r'\brapped\b': 'wrap',  # "chicken rapped" -> "chicken wrap"
            r'\bsole\b(?! of| shoe)': 'sole',  # fish, keep as is
            r'\bsoul food\b': 'soul food',  # Keep as is
            r'\bbean\b': 'bean',  # Keep as is
            r'\bbeen\b(?= salad| soup)': 'bean',  # "been salad" -> "bean salad"
            r'\bleak\b(?! soup)': 'leek',  # vegetable
            r'\bleek\b': 'leek',  # "ate a leek" vegetable
            r'\bwaist\b': 'waste',  # Usually not in food context
            r'\bwaste food\b': 'waste food',  # Keep as is
            r'\bcurrent\b(?= jelly| jam)': 'currant',  # "current jelly" -> "currant jelly"
            r'\btea\b': 'tea',  # Keep as is
            r'\btee\b(?! shirt| time)': 'tea',  # "cup of tee" -> "cup of tea"
            r'\bsuite\b(?= potato)': 'sweet',  # "suite potato" -> "sweet potato"
            r'\bsweet\b': 'sweet',  # Keep as is
            r'\byolk\b': 'yolk',  # egg yolk, keep as is
            r'\byoke\b(?= of)': 'yolk',  # "yoke of an egg" -> "yolk of an egg"
            r'\bmussel\b': 'mussel',  # seafood, keep as is
            r'\bmuscle\b(?= soup| dish)': 'mussel',  # "muscle soup" -> "mussel soup"
            r'\bthyme\b': 'thyme',  # herb, keep as is
            r'\btime\b(?= herb| spice)': 'thyme',  # "time herb" -> "thyme herb"
            r'\bcarat\b(?! gold)': 'carrot',  # "ate a carat" -> "ate a carrot"
            r'\bcarrot\b': 'carrot',  # Keep as is
            r'\blettuce\b': 'lettuce',  # Keep as is
            r'\blet us\b(?= salad| wrap)': 'lettuce',  # "let us salad" -> "lettuce salad"
            r'\bsource\b': 'sauce',  # "tomato source" -> "tomato sauce"
            r'\broll\b(?! call| up| down| over)': 'roll',  # Keep bread roll as is
            r'\brole\b(?= with| and| for)': 'roll',  # "dinner role" -> "dinner roll"
            r'\bjam\b': 'jam',  # Keep as is
            r'\bjamb\b': 'jam',  # Door jamb unlikely in food context
            r'\bpea\b': 'pea',  # Keep as is
            r'\bpee\b(?= soup| salad)': 'pea',  # "pee soup" -> "pea soup"
            r'\bwine\b': 'wine',  # Keep as is
            r'\bwhine\b(?! about)': 'wine',  # "red whine" -> "red wine"
            r'\bcorn\b': 'corn',  # Keep as is
            r'\bcorns\b(?! on)': 'corn',  # "ate corns" -> "ate corn"
            r'\brice\b': 'rice',  # Keep as is
            r'\brise\b(?= and| with| bowl)': 'rice',  # "bowl of rise" -> "bowl of rice"
            r'\bsale\b(?= dressing| on)': 'sale',  # Keep as is for context
            r'\bsail\b(?= dressing)': 'salad',  # "sail dressing" -> "salad dressing"
            r'\bcelery\b': 'celery',  # Keep as is
            r'\bsalary\b(?= sticks| soup)': 'celery',  # "salary sticks" -> "celery sticks"
            r'\bbowl\b': 'bowl',  # Keep as is
            r'\bbole\b': 'bowl',  # "bole of soup" -> "bowl of soup"
            r'\bcereal bowl\b': 'cereal bowl',  # Keep as is
            r'\bserial bowl\b': 'cereal bowl',  # Additional correction
            r'\bfair\b(?= amount| serving)': 'fair',  # Keep as is
            r'\bfare\b(?= well)': 'fare',  # Keep as is
            r'\bhare\b(?! krishna)': 'hair',  # Usually not food
            r'\bhair\b(?= soup| stew)': 'hare',  # "hair stew" -> "hare stew" (rabbit)

            # Dessert/Sweet food homophones
            r'\bit don\'t\b': 'a donut',  # "I ate it don't" -> "I ate a donut"
            r'\bit dont\b': 'a donut',  # "I ate it dont" -> "I ate a donut"
            r'\ba don\'t\b': 'a donut',  # "I ate a don't" -> "I ate a donut"
            r'\ba dont\b': 'a donut',  # "I ate a dont" -> "I ate a donut"
            r'\bdon\'t\b': 'donut',  # "don't" -> "donut"
            r'\bdont\b': 'donut',  # "dont" -> "donut"
            r'\bdo not\b': 'donut',  # "I ate a do not" -> "I ate a donut"
            r'\bdo nut\b': 'donut',  # "I ate a do nut" -> "I ate a donut"
            r'\bdoughnut\b': 'donut',  # Standardize spelling
            r'\bpie\b': 'pie',  # Keep as is
            r'\bpi\b(?! day| rate| symbol)': 'pie',  # "ate pi" -> "ate pie"
            r'\bcookie\b': 'cookie',  # Keep as is
            r'\bcooky\b': 'cookie',  # Alternative spelling
            r'\bbrownie\b': 'brownie',  # Keep as is
            r'\bbrowny\b': 'brownie',  # "ate a browny" -> "ate a brownie"
            r'\bcupcake\b': 'cupcake',  # Keep as is
            r'\bcup cake\b': 'cupcake',  # "cup cake" -> "cupcake"
            r'\bmuffin\b': 'muffin',  # Keep as is
            r'\bmuff in\b': 'muffin',  # "muff in" -> "muffin"
            r'\bscone\b': 'scone',  # Keep as is
            r'\bscoan\b': 'scone',  # "ate a scoan" -> "ate a scone"
            r'\bcandy\b': 'candy',  # Keep as is
            r'\bcandee\b': 'candy',  # "ate candee" -> "ate candy"
            r'\bchocolate\b': 'chocolate',  # Keep as is
            r'\bchock late\b': 'chocolate',  # "chock late" -> "chocolate"
            r'\bchock lit\b': 'chocolate',  # "chock lit" -> "chocolate"
            r'\bfudge\b': 'fudge',  # Keep as is
            r'\bjudge\b(?! judy| court)': 'fudge',  # "ate judge" -> "ate fudge"
            r'\bpudding\b': 'pudding',  # Keep as is
            r'\bputting\b(?! on| in| away)': 'pudding',  # "ate putting" -> "ate pudding"
            r'\btart\b': 'tart',  # Keep as is
            r'\btarte\b': 'tart',  # French spelling -> English
            r'\btorte\b': 'torte',  # Keep as is (different from tart)
            r'\btort\b(?! law| case)': 'torte',  # "chocolate tort" -> "chocolate torte"

            # Measurement homophones
            r'\bpeace of\b': 'piece of',  # "one peace of cake" -> "one piece of cake"
            r'\bpeaces of\b': 'pieces of',
            r'\bhole pizza\b': 'whole pizza',
            r'\bhole sandwich\b': 'whole sandwich',
            r'\bhole meal\b': 'whole meal',
            r'\bsum food\b': 'some food',
            r'\bsum carbs\b': 'some carbs',
            r'\boun\b': 'ounce',  # "one oun" -> "one ounce"
            r'\bounce\b': 'ounce',  # Keep as is
            r'\bounces\b': 'ounces',  # Keep as is
            r'\btea spoon\b': 'teaspoon',  # "tea spoon" -> "teaspoon"
            r'\btable spoon\b': 'tablespoon',  # "table spoon" -> "tablespoon"
            r'\btsp\b': 'teaspoon',  # Abbreviation
            r'\btbsp\b': 'tablespoon',  # Abbreviation
            r'\bT\.\b': 'tablespoon',  # T. -> tablespoon
            r'\bt\.\b': 'teaspoon',  # t. -> teaspoon
            r'\bcup full\b': 'cupful',  # "cup full" -> "cupful"
            r'\bpint\b': 'pint',  # Keep as is
            r'\bpaint\b(?= of)': 'pint',  # "paint of milk" -> "pint of milk"
            r'\bquart\b': 'quart',  # Keep as is
            r'\bcourt\b(?= of)': 'quart',  # "court of juice" -> "quart of juice"
            r'\bgallon\b': 'gallon',  # Keep as is
            r'\bgalleon\b(?= of)': 'gallon',  # "galleon of milk" -> "gallon of milk"
            r'\bliter\b': 'liter',  # Keep as is
            r'\bleader\b(?= of)': 'liter',  # "leader of soda" -> "liter of soda"
            r'\bmilliliter\b': 'milliliter',  # Keep as is
            r'\bml\b': 'milliliter',  # Abbreviation
            r'\bmilli leader\b': 'milliliter',  # "milli leader" -> "milliliter"

            # Medical/Diabetes-specific homophones
            r'\binsulin doze\b': 'insulin dose',
            r'\binsulin does\b': 'insulin dose',  # "insulin does" -> "insulin dose"
            r'\bdoes of insulin\b': 'dose of insulin',  # "does of insulin" -> "dose of insulin"
            r'\binjection sight\b': 'injection site',
            r'\binsulin vile\b': 'insulin vial',

            # Medical brand name corrections
            r'\blantiss\b': 'lantus',
            r'\blantiss\s+as\s+lovers\b': 'lantus dose',
            r'\blantus\s+as\s+lovers\b': 'lantus dose',
            r'\blantiss\s+doze\b': 'lantus dose',
            r'\b(\w+)\s+doze\b': '\\1 dose',  # Generic "doze" -> "dose" correction
            r'\blantiss\s+does\b': 'lantus dose',
            r'\blantiss\s+level\b': 'lantus level',
            r'\bwhat\'s\s+my\s+lantiss\b': 'what\'s my lantus',
            r'\bhumalog\b': 'humalog',  # Keep as is
            r'\bhuman\s+log\b': 'humalog',
            r'\bnovolog\b': 'novolog',  # Keep as is
            r'\bnovo\s+log\b': 'novolog',
            r'\btresiba\b': 'tresiba',  # Keep as is
            r'\bthe\s+siba\b': 'tresiba',
            r'\btree\s+siba\b': 'tresiba',
            r'\bapidra\b': 'apidra',  # Keep as is
            r'\bappear\s+dra\b': 'apidra',
            r'\bfiasp\b': 'fiasp',  # Keep as is
            r'\bfee\s+asp\b': 'fiasp',
            r'\blevemir\b': 'levemir',  # Keep as is
            r'\blever\s+meer\b': 'levemir',
            r'\blev\s+a\s+meer\b': 'levemir',
            r'\bbasaglar\b': 'basaglar',  # Keep as is
            r'\bbase\s+ag\s+lar\b': 'basaglar',

            r'\bglue coats\b': 'glucose',
            r'\bglue coat\b': 'glucose',
            r'\bblood sugar is hi\b': 'blood sugar is high',  # "hi" -> "high"
            r'\bsugar is hi\b': 'sugar is high',
            r'\bglucose is hi\b': 'glucose is high',
            r'\bhi blood sugar\b': 'high blood sugar',
            r'\bhi glucose\b': 'high glucose',
            r'\bblood sugar is lo\b': 'blood sugar is low',  # "lo" -> "low"
            r'\bsugar is lo\b': 'sugar is low',
            r'\bglucose is lo\b': 'glucose is low',
            r'\blo blood sugar\b': 'low blood sugar',
            r'\blo glucose\b': 'low glucose',
            r'\bbolus doze\b': 'bolus dose',  # "bolus doze" -> "bolus dose"
            r'\bbasal doze\b': 'basal dose',
            r'\bbolus does\b': 'bolus dose',
            r'\bbasal does\b': 'basal dose',
            r'\btest strips\b': 'test strips',  # Keep as is
            r'\btest trips\b': 'test strips',  # "test trips" -> "test strips"
            r'\blance it\b': 'lancet',  # "lance it" -> "lancet"
            r'\blance its\b': 'lancets',
            r'\bglue cometer\b': 'glucometer',  # "glue cometer" -> "glucometer"
            r'\bglue co meter\b': 'glucometer',
            r'\bcarb ratio\b': 'carb ratio',  # Keep as is
            r'\bcarb ration\b': 'carb ratio',  # "carb ration" -> "carb ratio"
            r'\ba one c\b': 'a1c',  # "a one c" -> "a1c"
            r'\ba 1 c\b': 'a1c',
            r'\bhypo\b': 'hypo',  # Keep as is (hypoglycemia)
            r'\bhigh po\b': 'hypo',  # "high po" -> "hypo"
            r'\bhyper\b': 'hyper',  # Keep as is (hyperglycemia)
            r'\bhigh per\b': 'hyper',  # "high per" -> "hyper"

            # Common medical query corrections
            r'\bwhat\'s\s+my\s+(\w+)\s+as\s+lovers\b': 'what\'s my \\1 dose',
            r'\bwhat\'s\s+my\s+(\w+)\s+level\s+of\b': 'what\'s my \\1 level',
            r'\bhigh\s+above\s+but\s+my\s+study\s+level\b': 'how about my study level',
            r'\bmy\s+last\s+those\b': 'my last dose',
            r'\blast\s+those\s+of\b': 'last dose of',

            # Medical action homophones
            r'\bprick\b': 'prick',  # Keep as is (finger prick)
            r'\bprick finger\b': 'prick finger',  # Keep as is
            r'\bcheck\b': 'check',  # Keep as is
            r'\bcheque\b(?= blood| sugar| glucose)': 'check',  # "cheque blood sugar" -> "check blood sugar"
            r'\bcheque my\b': 'check my',  # "cheque my levels" -> "check my levels"
            r'\btest\b': 'test',  # Keep as is
            r'\btaste\b(?= blood| sugar| glucose)': 'test',  # "taste blood sugar" -> "test blood sugar"
            r'\bmeasure\b': 'measure',  # Keep as is
            r'\bmajor\b(?= blood| glucose)': 'measure',  # "major blood sugar" -> "measure blood sugar"
            r'\binject\b': 'inject',  # Keep as is
            r'\bin checked\b': 'inject',  # "in checked insulin" -> "inject insulin"
            r'\btake\b': 'take',  # Keep as is
            r'\bmake\b(?= insulin| reading)': 'take',  # "make insulin" -> "take insulin"
            r'\bcalibrate\b': 'calibrate',  # Keep as is
            r'\bcalibrated\b': 'calibrated',  # Keep as is
            r'\bscan\b': 'scan',  # Keep as is (CGM scan)
            r'\bscanned\b': 'scanned',  # Keep as is
            r'\bprime\b': 'prime',  # Keep as is (pump prime)
            r'\bprime pump\b': 'prime pump',  # Keep as is
            r'\bbolus\b': 'bolus',  # Keep as is
            r'\bbowl us\b': 'bolus',  # "bowl us insulin" -> "bolus insulin"
            r'\bbasal\b': 'basal',  # Keep as is
            r'\bbase all\b': 'basal',  # "base all rate" -> "basal rate"
            r'\brotate\b': 'rotate',  # Keep as is (injection site rotation)
            r'\brow tate\b': 'rotate',  # "row tate sites" -> "rotate sites"

            # Fix completely garbled phrases
            r'\blove three egg and one side or taste the record\b': 'log three eggs and one slice of toast for breakfast',
            r'\bi ate one lord breakfast hands and face\b': 'i ate one large breakfast sandwich',
            r'\blord breakfast\b': 'large breakfast',
            r'\bhands and face\b': 'sandwich',
            r'\bside or taste\b': 'slice of toast',
            r'\btaste the record\b': 'toast for breakfast',

            # Common verb homophones
            r'\bwait\b(?= my| the| for)': 'weight',  # "check my wait" -> "check my weight" (when followed by my/the/for)
            r'\bmy wait\b': 'my weight',  # "check my wait" -> "check my weight"
            r'\bthe wait\b(?! time| list| period)': 'the weight',  # "log the wait" -> "log the weight"
            r'\bpast\b(?= my| the| a)': 'passed',  # "past the test" -> "passed the test"
            r'\bpassed\b(?= hour| day| week| month)': 'past',  # "passed hour" -> "past hour"
            r'\bway\b(?= \d+| one| two| three| four| five| six| seven| eight| nine| ten)': 'weigh',  # "way 180" -> "weigh 180"
            r'\bi way\b': 'i weigh',  # "i way 150" -> "i weigh 150"
            r'\bweigh in\b': 'weigh in',  # Keep as is
            r'\bway in\b(?! to| the)': 'weigh in',  # "way in at 150" -> "weigh in at 150"
            r'\bset a time or\b': 'set a timer',  # Common misheard phrase
            r'\bset time or\b': 'set timer',
            r'\blog my wait\b': 'log my weight',
            r'\btrack my wait\b': 'track my weight',
            r'\brecord my wait\b': 'record my weight',
            r'\bread\b(?= the| my| a)': 'read',  # Keep as is (not bread)
            r'\bred\b(?= the| my| this| that)': 'read',  # "red the label" -> "read the label"
            r'\brite\b(?= down| it| this)': 'write',  # "rite down" -> "write down"
            r'\bright\b(?= down| it| this)': 'write',  # "right down" -> "write down" (context dependent)
            r'\bno\b(?= my| the)': 'know',  # "no my levels" -> "know my levels" (context dependent)
            r'\bnew\b(?= my| the)': 'knew',  # Context dependent
            r'\bhere\b(?= my| the| is)': 'hear',  # Context dependent
            r'\bhear is\b': 'here is',  # "hear is my reading" -> "here is my reading"

            # Action/Command homophones
            r'\bsea my\b': 'see my',  # "sea my glucose" -> "see my glucose"
            r'\bsea the\b': 'see the',  # "sea the graph" -> "see the graph"
            r'\bc my\b': 'see my',  # "c my levels" -> "see my levels"
            r'\bc the\b': 'see the',  # "c the data" -> "see the data"
            r'\bbrake\b(?= down| up)': 'break',  # "brake down" -> "break down"
            r'\bbreak\b(?= the| my)': 'break',  # Keep as is
            r'\bpaws\b(?= the| recording)': 'pause',  # "paws the timer" -> "pause the timer"
            r'\bpause\b': 'pause',  # Keep as is
            r'\bstart\b': 'start',  # Keep as is
            r'\bstop\b': 'stop',  # Keep as is
            r'\bbegin\b': 'begin',  # Keep as is
            r'\bend\b': 'end',  # Keep as is
            r'\bfinish\b': 'finish',  # Keep as is
            r'\bcomplete\b': 'complete',  # Keep as is
            r'\bcancel\b': 'cancel',  # Keep as is
            r'\bresume\b': 'resume',  # Keep as is
            r'\breset\b': 'reset',  # Keep as is
            r'\bclear\b': 'clear',  # Keep as is
            r'\bdelete\b': 'delete',  # Keep as is
            r'\bremove\b': 'remove',  # Keep as is
            r'\badd\b': 'add',  # Keep as is
            r'\bad\b(?= insulin| timer| food)': 'add',  # "ad insulin" -> "add insulin"
            r'\bsubtract\b': 'subtract',  # Keep as is
            r'\bminus\b': 'minus',  # Keep as is
            r'\bplus\b': 'plus',  # Keep as is
            r'\bequals\b': 'equals',  # Keep as is
            r'\bturn\b': 'turn',  # Keep as is
            r'\btern\b(?= on| off)': 'turn',  # "tern on" -> "turn on"
            r'\benable\b': 'enable',  # Keep as is
            r'\bdisable\b': 'disable',  # Keep as is
            r'\bopen\b': 'open',  # Keep as is
            r'\bclose\b': 'close',  # Keep as is
            r'\bclothes\b(?= the| app)': 'close',  # "clothes the app" -> "close the app"
        }

        # Context-aware corrections that need more complex logic
        self.context_patterns = [
            # Fix "delete/remove the [something] timer" patterns
            (r'(delete|remove|clear|cancel|stop|erase)\s+the\s+(\w+)\s+of\b', r'\1 the \2'),

            # Fix trailing "of" after timer-related words
            (r'(timer|timers|countdown|countdowns)\s+of\b', r'\1'),

            # Fix "all time or/of/are" -> "all timers"
            (r'\ball\s+time\s+(of|or|are|ares)\b', 'all timers'),
            # Fix "time are" -> "timers" when preceded by "all"
            (r'\ball\s+timer\b', 'all timers'),
        ]

        # Smart corrections for "eight" based on context
        self.smart_corrections = [
            # "eight" -> "I ate" when followed by food words but NOT units/insulin words
            (r'^eight\s+(?!units|more\s+units|unit\b)', 'I ate '),
            # Common food patterns with "eight"
            (r'^eight\s+(a|an|some|the)\s+', 'I ate \1 '),
            # Special case: "i hate the [food]" -> "i ate the [food]" (must come first)
            (r'^i\s+hate\s+the\s+(pizza|burger|hamburger|sandwich|apple|banana|orange|eggs?|toast|salad|chicken|pasta|rice|bread|bagel|cereal|yogurt|cheese|meat|fish|steak|bacon|sausage|pancakes?|waffles?|oatmeal|soup|fries|chips|cookie|cake|ice\s*cream|donut|doughnut|pie|brownie|muffin|candy|chocolate)\b', r'i ate the \1'),
            # "i hate" -> "i ate" when followed by food articles
            (r'^i\s+hate\s+(a|an|some)\s+', 'i ate \1 '),
            # "i hate [food]" -> "i ate [food]"
            (r'^i\s+hate\s+(pizza|burger|hamburger|sandwich|apple|banana|orange|eggs?|toast|salad|chicken|pasta|rice|bread|bagel|cereal|yogurt|cheese|meat|fish|steak|bacon|sausage|pancakes?|waffles?|oatmeal|soup|fries|chips|cookie|cake|ice\s*cream|donut|doughnut|pie|brownie|muffin|candy|chocolate)', 'i ate \1'),
            # "eight pizza/burger/etc" (common food words)
            (r'^eight\s+(pizza|burger|hamburger|sandwich|apple|banana|orange|eggs?|toast|salad|chicken|pasta|rice|bread|bagel|cereal|yogurt|cheese|meat|fish|steak|bacon|sausage|pancakes?|waffles?|oatmeal|soup|fries|chips|cookie|cake|ice\s*cream|donut|doughnut|pie|brownie|muffin|candy|chocolate)', 'I ate \1'),
            # "eight [number] [food]" patterns
            (r'^eight\s+(\d+)\s+(slices?|pieces?|cups?|bowls?|plates?)\s+of\s+', 'I ate \1 \2 of '),
            # "eight [food] for [meal]" patterns
            (r'^eight\s+(.+?)\s+for\s+(breakfast|lunch|dinner|snack)', 'I ate \1 for \2'),
        ]

        # Context-aware number word corrections
        self.number_corrections = [
            # "for/four" corrections based on context
            (r'\bfor\s+(slices?|pieces?|cups?|bowls?|plates?|servings?|portions?|grams?|ounces?|pounds?|carbs?|calories?|units?)\b', r'four \1'),
            (r'\bhad\s+for\s+', 'had four '),  # "I had for eggs" -> "I had four eggs"
            (r'\bate\s+for\s+', 'ate four '),  # "I ate for slices" -> "I ate four slices"
            (r'\btook\s+for\s+units', 'took four units'),

            # "too/to/two" corrections based on context
            (r'\btoo\s+(slices?|pieces?|cups?|bowls?|plates?|servings?|portions?|grams?|ounces?|pounds?|carbs?|calories?|units?|eggs?|apples?|bananas?|cookies?)\b', r'two \1'),
            (r'\bto\s+(slices?|pieces?|cups?|bowls?|plates?|servings?|portions?|grams?|ounces?|pounds?|carbs?|calories?|units?|eggs?|apples?|bananas?|cookies?)\b', r'two \1'),
            (r'\bhad\s+too\s+', 'had two '),  # "I had too eggs" -> "I had two eggs"
            (r'\bhad\s+to\s+', 'had two '),   # "I had to eggs" -> "I had two eggs"
            (r'\bate\s+too\s+', 'ate two '),  # "I ate too slices" -> "I ate two slices"
            (r'\bate\s+to\s+', 'ate two '),   # "I ate to slices" -> "I ate two slices"
            (r'\btook\s+too\s+units', 'took two units'),
            (r'\btook\s+to\s+units', 'took two units'),

            # "won/one" corrections based on context
            (r'\bwon\s+(slice|piece|cup|bowl|plate|serving|portion|gram|ounce|pound|carb|calorie|unit|egg|apple|banana|cookie)\b', r'one \1'),
            (r'\bhad\s+won\s+', 'had one '),
            (r'\bate\s+won\s+', 'ate one '),
            (r'\btook\s+won\s+unit', 'took one unit'),

            # "sex/six" corrections based on context
            (r'\bsex\s+(slices?|pieces?|cups?|bowls?|plates?|servings?|portions?|grams?|ounces?|pounds?|carbs?|calories?)\b', r'six \1'),
            (r'\bhad\s+sex\s+', 'had six '),
            (r'\bate\s+sex\s+', 'ate six '),

            # "tree/three" corrections based on context
            (r'\btree\s+(slices?|pieces?|cups?|bowls?|plates?|servings?|portions?|grams?|ounces?|pounds?|carbs?|calories?|eggs?|apples?|bananas?|cookies?)\b', r'three \1'),
            (r'\bhad\s+tree\s+', 'had three '),
            (r'\bate\s+tree\s+', 'ate three '),
            (r'\btook\s+tree\s+units', 'took three units'),

            # "ate/eight" corrections for non-food contexts (inverse of the smart correction)
            (r'\bate\s+(o\'clock|am|pm|thirty|forty-five|fifteen)\b', r'eight \1'),  # "ate o'clock" -> "eight o'clock"
            (r'\bat\s+ate\b', 'at eight'),  # "at ate" -> "at eight"

            # Time of day homophones
            (r'\bknight\b(?= time| shift)', 'night'),  # "knight time" -> "night time"
            (r'\bnight\b', 'night'),  # Keep as is
            (r'\bmourning\b(?= glucose| reading| insulin)', 'morning'),  # "mourning glucose" -> "morning glucose"
            (r'\bmorning\b', 'morning'),  # Keep as is
            (r'\bevening\b', 'evening'),  # Keep as is
            (r'\beave ning\b', 'evening'),  # "eave ning" -> "evening"
            (r'\bdawn\b', 'dawn'),  # Keep as is
            (r'\bdon\b(?= glucose| reading)', 'dawn'),  # "don glucose" -> "dawn glucose" (dawn phenomenon)
            (r'\bdusk\b', 'dusk'),  # Keep as is
            (r'\bnoon\b', 'noon'),  # Keep as is
            (r'\bnewn\b', 'noon'),  # "newn" -> "noon"
            (r'\bmidnight\b', 'midnight'),  # Keep as is
            (r'\bmid knight\b', 'midnight'),  # "mid knight" -> "midnight"
            (r'\bweek\b', 'week'),  # Keep as is
            (r'\bweak\b(?= ago| from| before)', 'week'),  # "weak ago" -> "week ago"
            (r'\bdays\b', 'days'),  # Keep as is
            (r'\bdaze\b(?= ago| from)', 'days'),  # "daze ago" -> "days ago"
            (r'\bhour\b', 'hour'),  # Keep as is
            (r'\bour\b(?= ago| from)', 'hour'),  # "our ago" -> "hour ago"
            (r'\bminute\b', 'minute'),  # Keep as is
            (r'\bminit\b', 'minute'),  # "minit" -> "minute"

            # "nein/nine" corrections based on context
            (r'\bnein\s+(slices?|pieces?|cups?|bowls?|plates?|servings?|portions?|grams?|ounces?|pounds?|carbs?|calories?)\b', r'nine \1'),
            (r'\bhad\s+nein\s+', 'had nine '),
            (r'\bate\s+nein\s+', 'ate nine '),

            # Special case: preserve "for breakfast/lunch/dinner"
            (r'four\s+(breakfast|lunch|dinner|snack)', r'for \1'),
            # Special case: preserve "too much/many"
            (r'two\s+(much|many)', r'too \1'),
            # Special case: preserve "one more" (not "won more")
            (r'\bwon\s+more\s+', 'one more '),
        ]

    def process(self, text: str) -> str:
        """
        Process STT output to fix common misrecognitions

        Args:
            text: Raw STT output

        Returns:
            Corrected text
        """
        if not text:
            return text

        processed = text.lower().strip()

        # Apply simple replacements
        for pattern, replacement in self.corrections.items():
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # Apply context-aware patterns
        for pattern, replacement in self.context_patterns:
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # Apply smart corrections for "eight"
        for pattern, replacement in self.smart_corrections:
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # Apply number word corrections for "for/four" and "too/to/two"
        for pattern, replacement in self.number_corrections:
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # Clean up extra spaces
        processed = ' '.join(processed.split())

        # Remove common STT noise/artifacts at the end
        noise_patterns = [
            r'\s+(boys?\s+matt?|voice\s+matt?|boys?\s+max|boys?\s+match)$',  # Common noise patterns
            r'\s+(okay|ok|alright|right|yeah|yes|yep|nope|no|um|uh|ah|oh|hmm)$',  # Filler words at end
            r'\s+(please|thanks|thank\s+you)$',  # Politeness that confuses parsing
            r'\s+(now|today|tonight|tomorrow)$',  # Time words that aren't part of command
        ]

        for pattern in noise_patterns:
            processed = re.sub(pattern, '', processed, flags=re.IGNORECASE)

        return processed

    def get_confidence_boost_words(self) -> List[str]:
        """
        Get words that should have boosted confidence in STT
        These are words that are often misheard but critical for functionality
        """
        return [
            'timer', 'timers',
            'insulin', 'correction',
            'delete', 'remove', 'clear', 'cancel',
            'countdown', 'countdowns',
            'units', 'carbs', 'grams'
        ]


# Singleton instance
_processor = None


def get_stt_processor() -> STTPostProcessor:
    """Get or create the singleton STT post-processor"""
    global _processor
    if _processor is None:
        _processor = STTPostProcessor()
    return _processor


def correct_stt_output(text: str) -> str:
    """
    Convenience function to correct STT output

    Args:
        text: Raw STT output

    Returns:
        Corrected text
    """
    processor = get_stt_processor()
    return processor.process(text)
