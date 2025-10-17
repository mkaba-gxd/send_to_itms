import os
import pandas as pd
import datetime
from pathlib import Path
from .subfunc import *

def run_sendData(args):

    listfile = args.listfile
    sample_id = args.sample
    directory = Path(args.directory)
    transfer = Path(args.transfer)
    preparation = args.preparation

    now = datetime.datetime.now()
    now_str = str(now.strftime("%Y%m%d%H%M%S"))

    if listfile is None :
        if sample_id is None :
            init('Incorrect argument specified.')
        else :
            sample_id = [x.strip() for x in sample_id.split(',') if not x.strip() == '']
    elif not os.path.isfile(listfile) :
        init('List file does not exist.')
    else :
        with open(listfile, 'r') as f:
            try:
                sample_id = f.read().splitlines()
            except FileNotFoundError as e:
                init(e)

    sample_id = rmdup_list(sample_id)
    print("Run for " + str(len(sample_id))  + " sample IDs.")

    batch_id = []
    anal_type = []
    timepoint = []
    patient_no = []
    title = []

    for sample in sample_id :
        b, a, t, p, l = search_info(sample, directory)
        batch_id   += [b]
        anal_type  += [a]
        timepoint  += [t]
        patient_no += [p]
        title      += [l]

    df = pd.DataFrame(dict(batch_id=batch_id, sample_id=sample_id, anal_type=anal_type, timepoint=timepoint, patient_no=patient_no, title=title))

    df_drop = df.dropna()
    if df_drop.shape[0] == 0 :
        init('No entries in database.')
    elif df.shape[0] != df_drop.shape[0] :
        missing = set(sample_id) - set(df_drop['sample_id'])
        print('missing data: [' + ','.join(missing) + ']')
        choice = prompt_choice("Continue? (yes[Y]/no[N]):", ['yes', 'y', 'no', 'n'])
        if choice in ['no', 'n'] :
            init('Abort process.')

    df_M3 = df_drop[ df_drop['title']=='MONSTAR-SCREEN-3' ]
    if df_M3.shape[0] == 0 :
        init('No match for M3 sample')
    elif df_drop.shape[0] != df_M3.shape[0] :
        missing = set(df_drop['sample_id']) - set(df_M3['sample_id'])
        print('Sample not M3: [' + ','.join(missing) + ']')
        choice = prompt_choice("Continue? (yes[Y]/no[N]):", ['yes', 'y', 'no', 'n'])
        if choice in ['no', 'n'] :
            init('Abort process.')

    df_drop = df_M3.sort_values('patient_no').reset_index(drop=True)

    for i, item in df_drop.iterrows() :

        rawDir = os.path.join(directory, item['anal_type'], item['batch_id'], item['sample_id'])

        if item['anal_type'] == 'eWES':
            linkDir = os.path.join(transfer, now_str, 'GxD', item['patient_no'], item['timepoint'], 'WES')
            FQ1 = os.path.realpath( os.path.join(rawDir,'Fastq',item['sample_id'] + '.tumour.R1.fastq.gz') )
            FQ2 = os.path.realpath( os.path.join(rawDir,'Fastq',item['sample_id'] + '.tumour.R2.fastq.gz') )
            BAM = os.path.join(rawDir,'Preprocessing','align',item['sample_id'] + '.tumour.aligned.bam')
            VCF = os.path.join(rawDir,'SNV','somatic',item['sample_id'] + '_mutect2_freebayes_lofreq_vote_res.exome.vcf')

            if preparation :
                FILES = [ FQ1, FQ2, BAM, VCF ]
            else :
                JSON = os.path.join(rawDir,'Summary',item['sample_id']+'.report.json')
                SUM = []
                for subname in ['cnv.exome', 'msi.exome', 'snv.exome', 'snv.target', 'tmb.exome'] :
                    SUM.append(os.path.join(rawDir,'Summary','.'.join([item['sample_id'],'summarized',subname,'tsv'])))
                FILES = [ FQ1, FQ2, BAM, VCF, JSON ] + SUM

        elif item['anal_type'] == 'WTS':
            linkDir = os.path.join(transfer, now_str, 'GxD', item['patient_no'], item['timepoint'], 'WTS')
            FQ1 = os.path.realpath( os.path.join(rawDir,'Fastq',item['sample_id'] + '.R1.fastq.gz') )
            FQ2 = os.path.realpath( os.path.join(rawDir,'Fastq',item['sample_id'] + '.R2.fastq.gz') )
            BAM = os.path.join(rawDir,'Expression','STAR_align_exp',item['sample_id'] + '.Aligned.sortedByCoord.out.bam')

            if preparation :
                FILES = [ FQ1, FQ2, BAM ]
            else :
                JSON = os.path.join(rawDir,'Summary',item['sample_id']+'.report.json')
                SUM = []
                for subname in ['expression', 'fusion', 'splice'] :
                    SUM.append(os.path.join(rawDir,'Summary','.'.join([item['sample_id'],'summarized',subname,'tsv'])))
                FILES = [ FQ1, FQ2, BAM, JSON ] + SUM

        else :
            df_drop = df_drop[ df_drop['sample_id']!=item['sample_id'] ]
            continue

        flag = create_link(linkDir, FILES)
        if flag :
            print('Link failed :' + item['sample_id'])
            remove_upstream(Path(linkDir), transfer)
            df_drop = df_drop[ df_drop['sample_id']!=item['sample_id'] ]
        else :
            if not preparation :
                ckspath = os.path.join(transfer, now_str, 'checksum.' + str(i))
                if item['anal_type'] == 'eWES':
                    Cmd = f"echo -ne '' > {ckspath} && cd {transfer}/{now_str} && md5sum GxD/{item['patient_no']}/{item['timepoint']}/WES/* > {ckspath} "
                elif item['anal_type'] == 'WTS':
                    Cmd = f"echo -ne '' > {ckspath} && cd {transfer}/{now_str} && md5sum GxD/{item['patient_no']}/{item['timepoint']}/WTS/* > {ckspath} "
                qsubCmd = f"/data1/apps/sge/bin/lx-amd64/qsub -N CS_{now_str} -q all.q -pe smp 6 -o /dev/null -e /dev/null << EOF\n{Cmd}\nEOF"
                os.system(qsubCmd)
                os.system("sleep 1")

    if df_drop.shape[0] == 0 :
        init("Link fails in all samples.")

    df_drop['batch_id'] = [ os.path.basename(i) for i in df_drop['batch_id'] ]
    try :
        df_drop[['batch_id','sample_id','patient_no']].to_csv(transfer / f"{now_str}.idx", sep='\t', index=False, header=False)
    except NameError:
        pass

    if not preparation :
        mgCmd = f"cd {transfer}/{now_str} && cat checksum.[0-9]* | sort -k2,2 > checksum.txt && rm checksum.[0-9]* && "
        calCmd = "FILE_NUM_CAL=\`ls -d GxD/*/*/* | cut -f4 -d '/' | sort | uniq -c | awk 'BEGIN{TOTAL=0}{if($2==\"WES\"){TOTAL+=10*$1}else if($2==\"WTS\"){TOTAL+=7*$1}}END{print TOTAL}'\` && "
        actCmd = "FILE_NUM_ACT=\`ls GxD/*/*/*/* | wc -l\` && "
        sumCmd = "FILE_NUM_SUM=\`cat checksum.txt | wc -l\` && "
        ckCmd = "if [ $FILE_NUM_CAL -ne $FILE_NUM_ACT ]; then echo 'Discrepancy in number of files.' >> error.log; mv GxD GxD_error; elif [ $FILE_NUM_SUM -ne $FILE_NUM_CAL ]; then echo 'Checksum missing' >> error.log; mv GxD GxD_error; fi "
        Cmd = mgCmd + calCmd + actCmd + sumCmd + ckCmd
        qsubCmd = f"/data1/apps/sge/bin/lx-amd64/qsub -hold_jid CS_{now_str} -N MG_{now_str} -q all.q -pe smp 2 -o /dev/null -e /dev/null << EOF\n{Cmd}\nEOF"
        os.system(qsubCmd)

    print("After confirming the completion of all jobs, transfer the created data with the following command.")
    print(f"rsync -avLzu {transfer}/{now_str}/GxD /media/usb/cap/")
    if not preparation :
        print(f"cat {transfer}/{now_str}/checksum.txt >> /media/usb/cap/checksum.txt")

