/* This file is part of the Multiagent Decision Process (MADP) Toolbox. 
 *
 * The majority of MADP is free software released under GNUP GPL v.3. However,
 * some of the included libraries are released under a different license. For 
 * more information, see the included COPYING file. For other information, 
 * please refer to the included README file.
 *
 * This file has been written and/or modified by the following people:
 *
 * Frans Oliehoek 
 * Matthijs Spaan 
 *
 * For contact information please see the included AUTHORS file.
 */

#include "MADPParser.h"
#include "ParserDPOMDPFormat_Spirit.h"
#include "ParserPOMDPFormat_Spirit.h"
#include "DecPOMDPDiscrete.h"
#include "POMDPDiscrete.h"

void MADPParser::Parse(DecPOMDPDiscrete *model)
{
    DPOMDPFormatParsing::ParserDPOMDPFormat_Spirit parser(model);
    parser.Parse();
}

void MADPParser::Parse(POMDPDiscrete *model)
{
    POMDPFormatParsing::ParserPOMDPFormat_Spirit parser(model);
    parser.Parse();
}
