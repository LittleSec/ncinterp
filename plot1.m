% 画单幅热力图，file是csv文件。
function plot1(file)
    csv = csvread(file);
    x = csv(1,2:end);
    y = csv(2:end,1);
    z = csv(2:end,2:end);
    imagesc(x,y,flipud(z));
    colormap('jet');
    colorbar;
end