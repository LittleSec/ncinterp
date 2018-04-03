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

function interpACSV(fileName, minute, savePath)
    csvOld = csvread(fileName);
    % steps = minutes/60;
    n = floor(60/minute);
    x = csvOld(1,2:end);
    y = csvOld(2:end,1);

    z = csvOld(2:end, 2:end);
    % ????¤æ????å¸??NaNï¼??????¥ç©ºï¼?©º?½é?è¦?????
    % ä¼??è®©è??¨è?å¤??ï¼??ä¸ºè?ä¸??è¾??ç¬???¨ç??¼é????????µã?
    % if (numel(z(isnan(z))) == 0)
    %     z(z==0)=NaN;
    % end
    f = griddedInterpolant({y,x},z,'cubic');
    % xq = min(x):steps:max(x);
    xq = linspace(min(x), max(x), (max(x)-min(x))*n+1);
    % yq = min(y):steps:max(y);
    yq = linspace(min(y), max(y), (max(y)-min(y))*n+1);
    yq = yq';
    zq = f({yq,xq});
    csvNew = [inf xq; yq zq];
    csvwrite(strcat(savePath,fileName),csvNew);
end


