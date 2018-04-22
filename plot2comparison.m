% 画两类热力图对比，一左一右，一般用于对比插值前后效果
% file0, file1都是csv文件
function plot2comparison(file0, file1)
    csv0 = csvread(file0);
    csv1 = csvread(file1);
    x0 = csv0(1,2:end);
    y0 = csv0(2:end,1);
    x1 = csv1(1,2:end);
    y1 = csv1(2:end,1);
    value0 = csv0(2:end,2:end);
    value1 = csv1(2:end,2:end);
    figure
    ax0 = subplot(1,2,1);
    imagesc(ax0,x0,y0,flipud(value0));
    ax1 = subplot(1,2,2);
    imagesc(ax1,x1,y1,flipud(value1));
    colormap('jet');
    % colorbar;
end