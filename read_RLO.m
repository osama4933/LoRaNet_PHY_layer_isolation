clear all
clc
close all

pkts_lost_arr = [];
% for fname = ["Data_log_15mbit_train.txt", "Data_log_15mbit_test.txt"]
% for fname = ["Data_log_5mbit_train.txt", "Data_log_5mbit_test1.txt", "Data_log_5mbit_test2.txt", "Data_log_5mbit_test3.txt"]
% for fname = ["BW_adap\DATA_LOG_10m_1.txt"]%["Data_log_2mbit_test.txt"]
sz = zeros(1,8);
sz_uc = zeros(1,8);
pkts_dec = zeros(1,8);
for fname = ["RLO_out_1m.txt"]%["Data_log_2mbit_test.txt"]
    % fileID = fopen('test_log.txt','r');
    fileID = fopen(char(fname),'r');

    count = 1;
    pkt_num = [];
    chan = [];
    shft = [];
    bit = [];
    while ~feof(fileID)
        tline = fgetl(fileID);
        C = strsplit(tline,',');
        if str2num(C{1}) == 8
            sz(8) = sz(8) + str2num(C{3});
%             sz_uc(8) = sz_uc(8) + str2num(C{4});
            pkts_dec(8) = pkts_dec(8) + 1;
        elseif str2num(C{1}) == 7
            sz(7) = sz(7) + str2num(C{3});
%             sz_uc(7) = sz_uc(7) + str2num(C{4});
            pkts_dec(7) = pkts_dec(7) + 1;
        elseif str2num(C{1}) == 6
            sz(6) = sz(6) + str2num(C{3});
%             sz_uc(6) = sz_uc(6) + str2num(C{4});
            pkts_dec(6) = pkts_dec(6) + 1;
        elseif str2num(C{1}) == 5
            sz(5) = sz(5) + str2num(C{3});
%             sz_uc(5) = sz_uc(5) + str2num(C{4});
            pkts_dec(5) = pkts_dec(5) + 1;
        elseif str2num(C{1}) == 4
            sz(4) = sz(4) + str2num(C{3});
%             sz_uc(4) = sz_uc(4) + str2num(C{4});
            pkts_dec(4) = pkts_dec(4) + 1;
        elseif str2num(C{1}) == 3
            sz(3) = sz(3) + str2num(C{3});
%             sz_uc(3) = sz_uc(3) + str2num(C{4});
            pkts_dec(3) = pkts_dec(3) + 1;
        elseif str2num(C{1}) == 2
            sz(2) = sz(2) + str2num(C{3});
%             sz_uc(2) = sz_uc(2) + str2num(C{4});
            pkts_dec(2) = pkts_dec(2) + 1;
        elseif str2num(C{1}) == 1
            sz(1) = sz(1) + str2num(C{3});
%             sz_uc(1) = sz_uc(1) + str2num(C{4});
            pkts_dec(1) = pkts_dec(1) + 1;
        end
                    
%         disp(tline)
    end
    fclose(fileID);
end
