csvu0 = csvread('2000-01-16, 5.01m u0.csv');
csvu1 = csvread('2000-01-16, 5.01m u1.csv');
csvv0 = csvread('2000-01-16, 5.01m v0.csv');
csvv1 = csvread('2000-01-16, 5.01m v1.csv');
x = csvu0(1,2:end);
y = csvu0(2:end,1);
x1 = csvu1(1,2:end);
y1 = csvu1(2:end,1);
u0= csvu0(2:end,2:end);
v0 = csvv0(2:end,2:end);
u1 = csvu1(2:end,2:end);
v1 = csvv1(2:end,2:end);

figure
ax0 = subplot(1,2,1);
quiver(ax0,x,y,u0,v0);
% title(ax1,'Subplot 1')
% ylabel(ax1,'Values from -1 to 1')
ax1 = subplot(1,2,2);
quiver(x1,y1,u1,v1);

csvow0 = csvread('2000-01-16, 5.01m ow0.csv');
csvow1 = csvread('2000-01-16, 5.01m ow1.csv');
ow0 = csvow0(2:end,2:end);
ow1 = csvow1(2:end,2:end);
figure
ax0 = subplot(1,2,1);
imagesc(ax0,x,y,flipud(ow0))
ax1 = subplot(1,2,2);
imagesc(ax1,x1,y1,flipud(ow1))
colorbar