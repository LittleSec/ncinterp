% param:
%   dirPath: dictionary which the source file in, eg. /Users/littlesec/Desktop/relative humidity1960-2017_grid_(13x13)/
%   resolution: How many minutes have a value after interp
%   savePath: dictionary which the target file in, eg. /Users/littlesec/Desktop/relative humidity1960-2017_grid_(130x130)/
% attention:
%   resolution and savePath should be consistent, the caller should make sure this work.
%   In csv file, if a point without value, please fill with NaN, the caller would better done this work.

% I think the operation of file should done by caller(Python)
% If use the interpADir function, please new a 'interpADir.m' file

% function interpADir(dirPath, resolution, savePath)
%     cd dirPath
%     fileExt = '*.csv';  
%     files = dir(fullfile(dirPath,fileExt));  
%     len = size(files, 1);  
%     for i = 1:len
%         interpACSV(files(i,1).name, resolution, savePath);
%     end
% end

function interpACSV(fileName, resolution, savePath)
    csvOld = csvread(fileName);
    steps = resolution/60
    x = csvOld(1,2:end);
    y = csvOld(2:end,1);

    z = csvOld(2:end, 2:end);
    % 考虑判断是否带有NaN，还是直接空，空白需要替换。
    % 优先让调用者处理，因为这个逻辑不符合全网格都有值的情况。
    % if (numel(z(isnan(z))) == 0)
    %     z(z==0)=NaN;
    f = griddedInterpolant({y,x},z,'cubic');
    xq = min(x):steps:max(x);
    yq = min(y):steps:max(y);
    yq = yq';
    zq = f({yq,xq});
    csvNew = [inf xq; yq zq];
    csvwrite(strcat(savePath,fileName),csvNew);
end


